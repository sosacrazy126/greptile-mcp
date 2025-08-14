/**
 * Quicksort Algorithm Implementation in JavaScript
 * 
 * Quicksort is a highly efficient divide-and-conquer sorting algorithm.
 * It works by selecting a 'pivot' element and partitioning the array
 * around the pivot, then recursively sorting the sub-arrays.
 * 
 * Time Complexity:
 * - Best Case: O(n log n)
 * - Average Case: O(n log n) 
 * - Worst Case: O(n²) - when pivot is always the smallest/largest element
 * 
 * Space Complexity: O(log n) - due to recursive call stack
 */

/**
 * Main quicksort function with multiple pivot strategies
 * @param {number[]} arr - Array to sort
 * @param {string} pivotStrategy - 'first', 'last', 'middle', 'random', or 'median3'
 * @returns {number[]} - Sorted array (new array, original unchanged)
 */
function quicksort(arr, pivotStrategy = 'median3') {
    // Create a copy to avoid mutating the original array
    const sortedArray = [...arr];
    quicksortInPlace(sortedArray, 0, sortedArray.length - 1, pivotStrategy);
    return sortedArray;
}

/**
 * In-place quicksort implementation
 * @param {number[]} arr - Array to sort in place
 * @param {number} low - Starting index
 * @param {number} high - Ending index
 * @param {string} pivotStrategy - Pivot selection strategy
 */
function quicksortInPlace(arr, low, high, pivotStrategy = 'median3') {
    if (low < high) {
        // Partition the array and get the pivot index
        const pivotIndex = partition(arr, low, high, pivotStrategy);
        
        // Recursively sort elements before and after partition
        quicksortInPlace(arr, low, pivotIndex - 1, pivotStrategy);
        quicksortInPlace(arr, pivotIndex + 1, high, pivotStrategy);
    }
}

/**
 * Partition function using Lomuto partition scheme
 * @param {number[]} arr - Array to partition
 * @param {number} low - Starting index
 * @param {number} high - Ending index
 * @param {string} pivotStrategy - Pivot selection strategy
 * @returns {number} - Final position of pivot element
 */
function partition(arr, low, high, pivotStrategy) {
    // Choose pivot based on strategy
    const pivotIndex = choosePivot(arr, low, high, pivotStrategy);
    
    // Move pivot to end for Lomuto partitioning
    swap(arr, pivotIndex, high);
    const pivot = arr[high];
    
    // Index of smaller element (indicates right position of pivot)
    let i = low - 1;
    
    for (let j = low; j < high; j++) {
        // If current element is smaller than or equal to pivot
        if (arr[j] <= pivot) {
            i++;
            swap(arr, i, j);
        }
    }
    
    // Place pivot in correct position
    swap(arr, i + 1, high);
    return i + 1;
}

/**
 * Choose pivot based on different strategies
 * @param {number[]} arr - Array
 * @param {number} low - Starting index
 * @param {number} high - Ending index
 * @param {string} strategy - Pivot selection strategy
 * @returns {number} - Index of chosen pivot
 */
function choosePivot(arr, low, high, strategy) {
    switch (strategy) {
        case 'first':
            return low;
        case 'last':
            return high;
        case 'middle':
            return Math.floor((low + high) / 2);
        case 'random':
            return Math.floor(Math.random() * (high - low + 1)) + low;
        case 'median3':
        default:
            return medianOfThree(arr, low, high);
    }
}

/**
 * Median-of-three pivot selection (often provides better performance)
 * @param {number[]} arr - Array
 * @param {number} low - Starting index
 * @param {number} high - Ending index
 * @returns {number} - Index of median element
 */
function medianOfThree(arr, low, high) {
    const mid = Math.floor((low + high) / 2);
    
    if (arr[mid] < arr[low]) swap(arr, low, mid);
    if (arr[high] < arr[low]) swap(arr, low, high);
    if (arr[high] < arr[mid]) swap(arr, mid, high);
    
    return mid;
}

/**
 * Swap two elements in an array
 * @param {number[]} arr - Array
 * @param {number} i - First index
 * @param {number} j - Second index
 */
function swap(arr, i, j) {
    [arr[i], arr[j]] = [arr[j], arr[i]];
}

/**
 * Iterative quicksort implementation (avoids recursion stack overflow)
 * @param {number[]} arr - Array to sort
 * @returns {number[]} - Sorted array (new array, original unchanged)
 */
function quicksortIterative(arr) {
    const result = [...arr];
    const stack = [];
    
    // Push initial values onto stack
    stack.push(0);
    stack.push(result.length - 1);
    
    while (stack.length > 0) {
        const high = stack.pop();
        const low = stack.pop();
        
        if (low < high) {
            const pivotIndex = partition(result, low, high, 'median3');
            
            // Push left subarray bounds
            stack.push(low);
            stack.push(pivotIndex - 1);
            
            // Push right subarray bounds
            stack.push(pivotIndex + 1);
            stack.push(high);
        }
    }
    
    return result;
}

/**
 * Utility function to check if array is sorted
 * @param {number[]} arr - Array to check
 * @returns {boolean} - True if sorted in ascending order
 */
function isSorted(arr) {
    for (let i = 1; i < arr.length; i++) {
        if (arr[i] < arr[i - 1]) {
            return false;
        }
    }
    return true;
}

/**
 * Generate random array for testing
 * @param {number} size - Size of array
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {number[]} - Random array
 */
function generateRandomArray(size, min = 0, max = 1000) {
    return Array.from({ length: size }, () => 
        Math.floor(Math.random() * (max - min + 1)) + min
    );
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        quicksort,
        quicksortInPlace,
        quicksortIterative,
        partition,
        choosePivot,
        medianOfThree,
        swap,
        isSorted,
        generateRandomArray
    };
}

// Example usage and demonstrations
if (typeof window === 'undefined' && require.main === module) {
    console.log('🚀 Quicksort Algorithm Demonstrations\n');
    
    // Test with different arrays
    const testArrays = [
        [64, 34, 25, 12, 22, 11, 90],
        [5, 2, 8, 1, 9],
        [1],
        [],
        [3, 3, 3, 3],
        [5, 4, 3, 2, 1],
        generateRandomArray(20, 1, 100)
    ];
    
    testArrays.forEach((arr, index) => {
        console.log(`Test ${index + 1}: [${arr.join(', ')}]`);
        
        const sorted = quicksort(arr);
        console.log(`Sorted:   [${sorted.join(', ')}]`);
        console.log(`Is sorted: ${isSorted(sorted)}`);
        console.log('---');
    });
    
    // Performance comparison
    console.log('\n⚡ Performance Test (10,000 elements):');
    const largeArray = generateRandomArray(10000);
    
    console.time('Quicksort (Recursive)');
    const sorted1 = quicksort(largeArray);
    console.timeEnd('Quicksort (Recursive)');
    
    console.time('Quicksort (Iterative)');
    const sorted2 = quicksortIterative(largeArray);
    console.timeEnd('Quicksort (Iterative)');
    
    console.log(`Both results identical: ${JSON.stringify(sorted1) === JSON.stringify(sorted2)}`);
}
