import threading
import time
from typing import List

class SumCalculator:
    def __init__(self):
        self.results = {}
        self.lock = threading.Lock()
    
    def calculate_sum(self, start: int, end: int, thread_name: str) -> int:
        """
        Calculate sum of numbers from start to end (inclusive)
        """
        total = 0
        print(f"Thread '{thread_name}' starting calculation from {start} to {end}")
        
        for i in range(start, end + 1):
            total += i
        
        # Use lock to safely store result
        with self.lock:
            self.results[thread_name] = total
            print(f"Thread '{thread_name}' completed: sum from {start} to {end} = {total}")
        
        return total

def printToScreen(start: int, end:int, thread_name: str):

    for i in range(start, end):
        print(f"'{thread_name}', value='{i}'")
        time.sleep(1)
    


def main():

    # 1 10
    # 30 40
    # no thread: 20 seconds
    # with thread: 10 seconds


    # printToScreen(1, 10,"")

    # printToScreen(30, 40,"")

    # INSERT_YOUR_CODE

    # Use threading to run printToScreen(1, 10, "") and printToScreen(30, 40, "") in parallel

    thread1 = threading.Thread(target=printToScreen, args=(1, 10, "Thread-1"))
    thread2 = threading.Thread(target=printToScreen, args=(30, 40, "Thread-2"))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    print("FINISH")


    # print("=== Threading Example: Parallel Sum Calculation ===")
    # print()
    
    # # Create calculator instance
    # calculator = SumCalculator()
    
    # # Record start time
    # start_time = time.time()
    
    # # Create threads
    # thread1 = threading.Thread(
    #     target=calculator.calculate_sum,
    #     args=(1, 1000, "Thread-1"),
    #     name="Thread-1"
    # )
    
    # thread2 = threading.Thread(
    #     target=calculator.calculate_sum,
    #     args=(1001, 2000, "Thread-2"),
    #     name="Thread-2"
    # )
    
    # print("Starting both threads...")
    # print()
    
    # # Start threads
    # thread1.start()
    # thread2.start()
    
    # # Wait for both threads to complete
    # print("Waiting for threads to complete...")
    # thread1.join()
    # thread2.join()
    
    # # Record end time
    # end_time = time.time()
    
    # print()
    # print("=== Results ===")
    
    # # Get results from both threads
    # sum1 = calculator.results.get("Thread-1", 0)
    # sum2 = calculator.results.get("Thread-2", 0)
    # total_sum = sum1 + sum2
    
    # print(f"Thread-1 result (1-1000): {sum1:,}")
    # print(f"Thread-2 result (1001-2000): {sum2:,}")
    # print(f"Combined result (1-2000): {total_sum:,}")
    # print(f"Execution time: {end_time - start_time:.4f} seconds")
    
    # # Verify the result
    # expected_sum = sum(range(1, 2001))
    # print(f"Expected result: {expected_sum:,}")
    # print(f"Result is {'CORRECT' if total_sum == expected_sum else 'INCORRECT'}")
    
    # print()
    # print("=== Comparison with Single Thread ===")
    
    # # Single thread execution for comparison
    # start_time_single = time.time()
    # single_result = sum(range(1, 2001))
    # end_time_single = time.time()
    
    # print(f"Single thread result: {single_result:,}")
    # print(f"Single thread time: {end_time_single - start_time_single:.4f} seconds")
    # print(f"Speedup: {(end_time_single - start_time_single) / (end_time - start_time):.2f}x")

def demonstrate_thread_lifecycle():
    """
    Additional demonstration of thread lifecycle and synchronization
    """
    print("\n=== Thread Lifecycle Demonstration ===")
    
    def worker_function(worker_id: int, work_items: List[str]):
        print(f"Worker {worker_id} started")
        for i, item in enumerate(work_items):
            print(f"Worker {worker_id} processing item {i+1}: {item}")
            time.sleep(0.1)  # Simulate work
        print(f"Worker {worker_id} finished")
    
    # Create work items
    work_items_1 = ["Task-A", "Task-B", "Task-C"]
    work_items_2 = ["Task-X", "Task-Y", "Task-Z"]
    
    # Create and start threads
    worker1 = threading.Thread(target=worker_function, args=(1, work_items_1))
    worker2 = threading.Thread(target=worker_function, args=(2, work_items_2))
    
    print("Starting workers...")
    worker1.start()
    worker2.start()
    
    # Wait for completion
    worker1.join()
    worker2.join()
    print("All workers completed!")

if __name__ == "__main__":
    # Run main threading example
    main()
    
    # Run additional demonstration
    # demonstrate_thread_lifecycle()
    
    # print("\n=== Threading Concepts Explained ===")
    # print("1. Thread Creation: threading.Thread() creates a new thread")
    # print("2. Thread Start: thread.start() begins thread execution")
    # print("3. Thread Join: thread.join() waits for thread to complete")
    # print("4. Thread Safety: threading.Lock() prevents race conditions")
    # print("5. Parallel Execution: Multiple threads run simultaneously")
    # print("6. Shared Resources: Threads can share data safely with locks")
