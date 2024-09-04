import redis
from urllib.parse import urlparse
import sys
import csv
from datetime import datetime
from datetime import datetime, timezone

def redis_id_to_iso8601(redis_id):
    # Split the ID into its timestamp and sequence number parts
    parts = redis_id.split('-')
    if len(parts) != 2:
        raise ValueError("Invalid Redis stream ID format")

    # Extract the timestamp (in milliseconds)
    timestamp_ms = int(parts[0])

    # Convert milliseconds to seconds
    timestamp_s = timestamp_ms / 1000.0

    # Create a datetime object
    dt = datetime.fromtimestamp(timestamp_s, tz=timezone.utc)

    # Format the datetime as ISO8601
    return dt.isoformat()

class BytesDecoder:
    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            method = getattr(self._obj, name)
            result = method(*args, **kwargs)
            if isinstance(result, bytes):
                return result.decode('utf-8')
            return result
        return wrapper
    
def get_latest_stream_id(r, stream_key):
    result = r.xrevrange(stream_key, count=1)
    if result:
        return result[0][0].decode('utf-8')
    return None

def get_stream_size(r, key):
    total_size = 0
    last_id = '0-0'
    while True:
        response = r.xrange(key, min=last_id, max='+', count=100)
        if not response:
            break
        for item_id, item_dict in response:
            print(f"Total size is {total_size}")
            # Calculate size of the ID
            total_size += len(item_id)
            # Calculate size of the item dictionary
            for field, value in item_dict.items():
                total_size += len(field)
                total_size += len(value)
        # Update last_id to be just after the last item's ID
        last_item_id = response[-1][0].decode('utf-8')
        timestamp, sequence = last_item_id.split('-')
        last_id = f"{timestamp}-{int(sequence) + 1}"
        
        print(f"Last ID is {last_id} repr {repr(last_id)}")
    return total_size

def to_csv(data, prefix):
    """
    Convert a list of lists to a CSV file with a timestamped filename.
    
    :param data: List of lists containing the data to be written to CSV
    :param prefix: Prefix for the filename
    :return: The name of the created CSV file
    """
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create filename
    filename = f"{prefix}_{timestamp}.csv"
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in data:
            # Convert all items in the row to strings
            string_row = [str(item) for item in row]
            writer.writerow(string_row)
    
    return filename

def get_largest_stream_keys(r):
    stream_keys = []
    r_raw = r
    r = BytesDecoder(r_raw)
    try:
        # Get all keys
        all_keys = r.keys('*')

        print("Total keys: %d" % len(all_keys))
        
        # Filter for stream keys and get their memory usage
        i = 0
        for key in all_keys:
            if i % 100 == 0:
                print("Progress: %.1f%%" % (100.0 * float(i) / float(len(all_keys))))
            i += 1
            if r.type(key) == 'stream':
                memory_usage = r.memory_usage(key)
                latest_id = get_latest_stream_id(r_raw, key)
                stream_keys.append((key, memory_usage, latest_id and redis_id_to_iso8601(latest_id) or "None"))
        
    except redis.RedisError as e:
        print(f"Error connecting to Redis: {e}")
    except:
        print(f"Eating exception and returning results so far")
    return stream_keys

def stream_mem_usage_to_csv(r, argv):
    stream_keys = get_largest_stream_keys(r)

    file_name = to_csv(stream_keys, "stream_sizes")
    print(f"Wrote file: {file_name}")

def get_stream_precise_size(r, argv):
    stream_key = argv[0]
    size = get_stream_size(r, stream_key)
    print(f"Exact size of {stream_key} is: {size}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <redis_url> [args...]")
        sys.exit(1)

    redis_url = sys.argv[1]
    
    # Parse the Redis URL
    parsed_url = urlparse(redis_url)
    host = parsed_url.hostname or 'localhost'
    port = parsed_url.port or 6379

    # Connect to Redis
    r = redis.Redis(host=host, port=port, decode_responses=False)

    # Call the body
    stream_mem_usage_to_csv(r, sys.argv[2:])
    # get_stream_precise_size(r, sys.argv[2:])
