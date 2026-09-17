import pandas as pd
import hashlib

def build_threads_from_dataframe(df: pd.DataFrame, target_brand: str = None) -> list:
    """
    Reconstructs conversational threads from the raw dataframe.
    """
    df_subset = df[['tweet_id', 'author_id', 'inbound', 'created_at', 'text', 'in_response_to_tweet_id']].copy()
    df_subset['in_response_to_tweet_id'] = df_subset['in_response_to_tweet_id'].fillna('')
    
    # Sort chronologically early to ensure message arrays are ordered correctly when traversed
    df_subset['created_at_dt'] = pd.to_datetime(df_subset['created_at'], errors='coerce')
    df_subset = df_subset.sort_values('created_at_dt')
    
    records = df_subset.to_dict('records')
    
    tweet_dict = {}
    parent_to_children = {}
    
    for r in records:
        tid = r['tweet_id']
        tweet_dict[tid] = r
        parent_id = r['in_response_to_tweet_id']
        if parent_id:
            if parent_id not in parent_to_children:
                parent_to_children[parent_id] = []
            parent_to_children[parent_id].append(tid)
            
    # Find roots
    roots = []
    for tid, r in tweet_dict.items():
        parent_id = r['in_response_to_tweet_id']
        if not parent_id or parent_id not in tweet_dict:
            roots.append(tid)
            
    threads = []
    
    for root_id in roots:
        stack = [root_id]
        visited = set()
        messages = []
        has_missing_parent = False
        branch_detected = False
        
        root_tweet = tweet_dict[root_id]
        if root_tweet['in_response_to_tweet_id'] and root_tweet['in_response_to_tweet_id'] not in tweet_dict:
            has_missing_parent = True
            
        while stack:
            curr_id = stack.pop()
            if curr_id in visited:
                continue # cycle detection
            visited.add(curr_id)
            messages.append(tweet_dict[curr_id])
            
            children = parent_to_children.get(curr_id, [])
            if len(children) > 1:
                branch_detected = True
                
            # append reversed so left-most child processes first
            for child_id in reversed(children):
                if child_id not in visited:
                    stack.append(child_id)
                    
        if len(messages) == 0:
            continue
            
        involves_brand = False
        if target_brand:
            for msg in messages:
                if msg['author_id'] == target_brand:
                    involves_brand = True
                    break
            if not involves_brand:
                continue
                
        # Calculate conversational turns
        turns = 1
        last_inbound = messages[0]['inbound']
        for msg in messages[1:]:
            if msg['inbound'] != last_inbound:
                turns += 1
                last_inbound = msg['inbound']
                
        # Clean up fields
        clean_messages = []
        for msg in messages:
            clean_msg = {k: v for k, v in msg.items() if k != 'created_at_dt'}
            clean_messages.append(clean_msg)
            
        # Deterministic Thread ID based on root
        hasher = hashlib.sha256()
        hasher.update(root_id.encode('utf-8'))
        thread_id = hasher.hexdigest()[:16]
        
        thread = {
            "thread_id": thread_id,
            "root_tweet_id": root_id,
            "messages": clean_messages,
            "metadata": {
                "message_count": len(clean_messages),
                "turn_count": turns,
                "has_missing_parent": has_missing_parent,
                "branch_detected": branch_detected
            }
        }
        threads.append(thread)
        
    return threads
