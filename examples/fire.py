from tasks import say

if __name__ == '__main__':
    for i in range(1, 100):
        print say.apply_async(('hello world', ), queue='popcorn')
