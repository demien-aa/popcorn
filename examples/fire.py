from tasks import say

if __name__ == '__main__':
    for i in range(1, 5000):
        print say.apply_async(('', ), queue='popcorn')
