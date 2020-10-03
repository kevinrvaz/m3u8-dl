from progress.bar import ChargingBar


def update_progress_bar(queue, length):
    bar = ChargingBar('Downloading ------------>', max=length)
    while True:
        try:
            data = queue.get()
            bar.next(data)
        except EOFError:
            pass
