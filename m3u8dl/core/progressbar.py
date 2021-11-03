from tqdm import tqdm
from time import sleep

def update_progress_bar(queue, length):
    with tqdm(total=length) as pbar:
        while True:
            try:
                data = queue.get()
                sleep(0.1)
                pbar.update(data)
            except EOFError:
                pass
