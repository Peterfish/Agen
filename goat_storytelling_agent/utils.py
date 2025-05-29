def split_into_words_w_newline(text):
    """Split text into words while preserving line structure"""
    if not text:
        return []
    lines = text.split('\n')
    split_text = [line.split(None) for line in lines if line]
    return split_text


def remove_last_n_words(text, n):
    """Remove last n words from text while preserving line breaks"""
    if not text or n <= 0:
        return text
        
    split_text = split_into_words_w_newline(text)
    if not split_text:
        return ""
        
    i = 1
    lines_to_slice = 0
    while n > 0 and i <= len(split_text):
        if i > len(split_text):
            break
        line = split_text[-i]
        if line:
            n_words = len(line)
            if n_words < n:
                n -= n_words
                lines_to_slice += 1
            else:
                split_text[-i] = line[:-n]
                break
        i += 1
        
    if lines_to_slice > 0:
        split_text = split_text[:-lines_to_slice]
    
    text = "\n".join([" ".join(line) for line in split_text])
    return text.strip()


def keep_last_n_words(text, n):
    """Keep only last n words from text while preserving line breaks"""
    if not text or n <= 0:
        return ""
        
    split_text = split_into_words_w_newline(text)
    if not split_text:
        return ""
        
    total_words = sum(len(line) for line in split_text)
    if total_words <= n:
        return text  # Return all text if it's shorter than n words
        
    words_found = 0
    result_lines = []
    
    # Process from the end
    for line in reversed(split_text):
        if not line:
            if words_found < n:
                result_lines.insert(0, [])
            continue
            
        line_words = len(line)
        if words_found + line_words <= n:
            result_lines.insert(0, line)
            words_found += line_words
        else:
            words_needed = n - words_found
            result_lines.insert(0, line[-words_needed:])
            break
    
    text = "\n".join([" ".join(line) for line in result_lines])
    return text.strip()
