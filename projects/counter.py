def get_next_count():
    try:
        with open('pdf_count.txt', 'r') as f:
            count = int(f.read().strip())
    except FileNotFoundError:
        count = 5
    
    next_count = count + 1
    
    with open('pdf_count.txt', 'w') as f:
        f.write(str(next_count))
    
    return next_count