"""
Code snippet dataset.
Each snippet has:
  - id: unique int
  - code: buggy Python function
  - bug_type: expected answer for easy task
  - bug_type_aliases: acceptable alternative phrasings
  - fixed_code: corrected function for medium task grader
  - test_cases: list of (args, expected_output) for medium grader
  - review: full review object for hard task grader
"""

SNIPPETS = [
    {
        "id": 0,
        "code": (
            "def sum_list(nums):\n"
            "    total = 0\n"
            "    for i in range(len(nums) + 1):\n"
            "        total += nums[i]\n"
            "    return total"
        ),
        "bug_type": "off-by-one error",
        "bug_type_aliases": ["index out of range", "off by one", "range error"],
        "fixed_code": (
            "def sum_list(nums):\n"
            "    total = 0\n"
            "    for i in range(len(nums)):\n"
            "        total += nums[i]\n"
            "    return total"
        ),
        "test_cases": [
            ([1, 2, 3], 6),
            ([10, 20], 30),
            ([0], 0),
            ([], 0),
        ],
        "review": {
            "bugs": [
                {"line": 3, "severity": "high", "description": "range(len(nums) + 1) causes IndexError on last iteration"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 3, "severity": "low", "description": "Use enumerate() or sum() instead of manual index loop"},
            ],
        },
    },
    {
        "id": 1,
        "code": (
            "def divide(a, b):\n"
            "    return a / b"
        ),
        "bug_type": "division by zero",
        "bug_type_aliases": ["zero division", "zerodivisionerror", "missing zero check"],
        "fixed_code": (
            "def divide(a, b):\n"
            "    if b == 0:\n"
            "        raise ValueError('Cannot divide by zero')\n"
            "    return a / b"
        ),
        "test_cases": [
            ((10, 2), 5.0),
            ((9, 3), 3.0),
            ((0, 5), 0.0),
        ],
        "review": {
            "bugs": [
                {"line": 2, "severity": "high", "description": "No guard against division by zero — raises ZeroDivisionError"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 1, "severity": "low", "description": "Missing docstring"},
            ],
        },
    },
    {
        "id": 2,
        "code": (
            "def find_max(nums):\n"
            "    max_val = 0\n"
            "    for n in nums:\n"
            "        if n > max_val:\n"
            "            max_val = n\n"
            "    return max_val"
        ),
        "bug_type": "wrong initial value",
        "bug_type_aliases": ["initialisation error", "initialization error", "incorrect default", "logic error"],
        "fixed_code": (
            "def find_max(nums):\n"
            "    if not nums:\n"
            "        raise ValueError('Empty list')\n"
            "    max_val = nums[0]\n"
            "    for n in nums:\n"
            "        if n > max_val:\n"
            "            max_val = n\n"
            "    return max_val"
        ),
        "test_cases": [
            ([3, 1, 4, 1, 5], 5),
            ([10, 20, 30], 30),
            ([-5, -1, -9], -1),
        ],
        "review": {
            "bugs": [
                {"line": 2, "severity": "high", "description": "Initialising max_val to 0 fails for all-negative lists"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 1, "severity": "low", "description": "No handling for empty input list"},
            ],
        },
    },
    {
        "id": 3,
        "code": (
            "import subprocess\n"
            "\n"
            "def run_command(user_input):\n"
            "    result = subprocess.run(user_input, shell=True, capture_output=True)\n"
            "    return result.stdout.decode()"
        ),
        "bug_type": "command injection",
        "bug_type_aliases": ["shell injection", "security vulnerability", "injection vulnerability"],
        "fixed_code": (
            "import subprocess\n"
            "\n"
            "def run_command(user_input):\n"
            "    allowed = {'ls', 'pwd', 'whoami'}\n"
            "    if user_input not in allowed:\n"
            "        raise ValueError('Command not allowed')\n"
            "    result = subprocess.run([user_input], shell=False, capture_output=True)\n"
            "    return result.stdout.decode()"
        ),
        "test_cases": [
            ("ls", str),   # just check it returns a string
        ],
        "review": {
            "bugs": [],
            "security_issues": [
                {"line": 4, "severity": "high", "description": "shell=True with unsanitised user_input allows OS command injection"},
                {"line": 4, "severity": "high", "description": "No input validation or whitelist — attacker can run any command"},
            ],
            "style_violations": [
                {"line": 3, "severity": "low", "description": "Missing docstring explaining expected input format"},
            ],
        },
    },
    {
        "id": 4,
        "code": (
            "def factorial(n):\n"
            "    if n == 0:\n"
            "        return 1\n"
            "    return n * factorial(n)"
        ),
        "bug_type": "infinite recursion",
        "bug_type_aliases": ["recursion error", "missing base case", "stack overflow", "wrong recursive call"],
        "fixed_code": (
            "def factorial(n):\n"
            "    if n == 0:\n"
            "        return 1\n"
            "    return n * factorial(n - 1)"
        ),
        "test_cases": [
            (0, 1),
            (1, 1),
            (5, 120),
            (6, 720),
        ],
        "review": {
            "bugs": [
                {"line": 4, "severity": "high", "description": "factorial(n) calls itself with same n — infinite recursion"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 1, "severity": "low", "description": "No guard for negative input"},
            ],
        },
    },
    {
        "id": 5,
        "code": (
            "def get_user(users, name):\n"
            "    for user in users:\n"
            "        if user['name'] == name:\n"
            "            return user\n"
            "    return None\n"
            "\n"
            "def print_email(users, name):\n"
            "    user = get_user(users, name)\n"
            "    print(user['email'])"
        ),
        "bug_type": "null pointer dereference",
        "bug_type_aliases": ["none dereference", "missing null check", "attributeerror", "typeerror on none"],
        "fixed_code": (
            "def get_user(users, name):\n"
            "    for user in users:\n"
            "        if user['name'] == name:\n"
            "            return user\n"
            "    return None\n"
            "\n"
            "def print_email(users, name):\n"
            "    user = get_user(users, name)\n"
            "    if user is None:\n"
            "        print('User not found')\n"
            "        return\n"
            "    print(user['email'])"
        ),
        "test_cases": [
            (([{"name": "Alice", "email": "a@b.com"}], "Alice"), None),
            (([{"name": "Alice", "email": "a@b.com"}], "Bob"), None),
        ],
        "review": {
            "bugs": [
                {"line": 9, "severity": "high", "description": "user['email'] crashes with TypeError if get_user returns None"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 7, "severity": "low", "description": "print_email should return or raise instead of silently doing nothing on failure"},
            ],
        },
    },
    {
        "id": 6,
        "code": (
            "def remove_duplicates(lst):\n"
            "    for i in range(len(lst)):\n"
            "        if lst[i] in lst[i+1:]:\n"
            "            lst.remove(lst[i])\n"
            "    return lst"
        ),
        "bug_type": "mutating list while iterating",
        "bug_type_aliases": ["list mutation during iteration", "concurrent modification", "index error during loop"],
        "fixed_code": (
            "def remove_duplicates(lst):\n"
            "    seen = set()\n"
            "    result = []\n"
            "    for item in lst:\n"
            "        if item not in seen:\n"
            "            seen.add(item)\n"
            "            result.append(item)\n"
            "    return result"
        ),
        "test_cases": [
            ([1, 2, 2, 3], [1, 2, 3]),
            ([1, 1, 1], [1]),
            ([1, 2, 3], [1, 2, 3]),
            ([], []),
        ],
        "review": {
            "bugs": [
                {"line": 4, "severity": "high", "description": "Modifying lst during iteration causes skipped elements and IndexError"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 1, "severity": "low", "description": "O(n²) approach — use a set for O(n) deduplication"},
            ],
        },
    },
    {
        "id": 7,
        "code": (
            "def is_palindrome(s):\n"
            "    return s == s[::-1]"
        ),
        "bug_type": "case sensitivity error",
        "bug_type_aliases": ["missing case normalisation", "case insensitive check missing", "logic error"],
        "fixed_code": (
            "def is_palindrome(s):\n"
            "    s = s.lower().replace(' ', '')\n"
            "    return s == s[::-1]"
        ),
        "test_cases": [
            ("racecar", True),
            ("Racecar", True),
            ("hello", False),
            ("A man a plan a canal Panama".replace(" ", "").lower(), True),
        ],
        "review": {
            "bugs": [
                {"line": 2, "severity": "medium", "description": "'Racecar' returns False — missing .lower() normalisation"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 2, "severity": "low", "description": "Spaces not stripped — 'race car' should be treated as palindrome"},
            ],
        },
    },
    {
        "id": 8,
        "code": (
            "def read_config(path):\n"
            "    f = open(path)\n"
            "    data = f.read()\n"
            "    return data"
        ),
        "bug_type": "resource leak",
        "bug_type_aliases": ["file not closed", "missing file close", "unclosed file handle"],
        "fixed_code": (
            "def read_config(path):\n"
            "    with open(path) as f:\n"
            "        data = f.read()\n"
            "    return data"
        ),
        "test_cases": [],  # file IO — grader checks code pattern
        "review": {
            "bugs": [
                {"line": 2, "severity": "medium", "description": "File handle never closed — resource leak on exception"},
            ],
            "security_issues": [
                {"line": 2, "severity": "medium", "description": "No path validation — could read arbitrary files (path traversal risk)"},
            ],
            "style_violations": [
                {"line": 2, "severity": "low", "description": "Use 'with open(path) as f:' for automatic resource management"},
            ],
        },
    },
    {
        "id": 9,
        "code": (
            "def binary_search(arr, target):\n"
            "    low, high = 0, len(arr)\n"
            "    while low < high:\n"
            "        mid = (low + high) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            low = mid\n"
            "        else:\n"
            "            high = mid - 1\n"
            "    return -1"
        ),
        "bug_type": "infinite loop",
        "bug_type_aliases": ["loop does not terminate", "low never advances", "logic error in loop"],
        "fixed_code": (
            "def binary_search(arr, target):\n"
            "    low, high = 0, len(arr) - 1\n"
            "    while low <= high:\n"
            "        mid = (low + high) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            low = mid + 1\n"
            "        else:\n"
            "            high = mid - 1\n"
            "    return -1"
        ),
        "test_cases": [
            (([1, 3, 5, 7, 9], 5), 2),
            (([1, 3, 5, 7, 9], 1), 0),
            (([1, 3, 5, 7, 9], 9), 4),
            (([1, 3, 5, 7, 9], 4), -1),
        ],
        "review": {
            "bugs": [
                {"line": 8, "severity": "high", "description": "low = mid never advances when arr[mid] < target — causes infinite loop"},
                {"line": 2, "severity": "medium", "description": "high = len(arr) is out of bounds — should be len(arr) - 1"},
            ],
            "security_issues": [],
            "style_violations": [],
        },
    },
    {
        "id": 10,
        "code": (
            "def count_words(sentence):\n"
            "    words = sentence.split(' ')\n"
            "    count = {}\n"
            "    for word in words:\n"
            "        count[word] == count.get(word, 0) + 1\n"
            "    return count"
        ),
        "bug_type": "wrong operator",
        "bug_type_aliases": ["comparison instead of assignment", "== instead of =", "assignment error"],
        "fixed_code": (
            "def count_words(sentence):\n"
            "    words = sentence.split(' ')\n"
            "    count = {}\n"
            "    for word in words:\n"
            "        count[word] = count.get(word, 0) + 1\n"
            "    return count"
        ),
        "test_cases": [
            ("hello world hello", {"hello": 2, "world": 1}),
            ("a a a", {"a": 3}),
            ("one", {"one": 1}),
        ],
        "review": {
            "bugs": [
                {"line": 5, "severity": "high", "description": "== is comparison not assignment — count never updates, returns empty dict"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 2, "severity": "low", "description": "split() without args handles multiple spaces better than split(' ')"},
            ],
        },
    },
    {
        "id": 11,
        "code": (
            "def flatten(lst):\n"
            "    result = []\n"
            "    for item in lst:\n"
            "        if isinstance(item, list):\n"
            "            result.append(flatten(item))\n"
            "        else:\n"
            "            result.append(item)\n"
            "    return result"
        ),
        "bug_type": "wrong method call",
        "bug_type_aliases": ["append instead of extend", "nested list not flattened", "logic error"],
        "fixed_code": (
            "def flatten(lst):\n"
            "    result = []\n"
            "    for item in lst:\n"
            "        if isinstance(item, list):\n"
            "            result.extend(flatten(item))\n"
            "        else:\n"
            "            result.append(item)\n"
            "    return result"
        ),
        "test_cases": [
            ([[1, [2, 3], 4]], [1, 2, 3, 4]),
            ([[1, 2, 3]], [1, 2, 3]),
            ([[[]]], []),
        ],
        "review": {
            "bugs": [
                {"line": 5, "severity": "high", "description": "append(flatten(item)) nests the list instead of extending — result contains sublists"},
            ],
            "security_issues": [],
            "style_violations": [],
        },
    },
    {
        "id": 12,
        "code": (
            "import pickle\n"
            "import os\n"
            "\n"
            "def load_user_data(filename):\n"
            "    with open(filename, 'rb') as f:\n"
            "        return pickle.load(f)"
        ),
        "bug_type": "insecure deserialization",
        "bug_type_aliases": ["pickle security vulnerability", "arbitrary code execution", "unsafe deserialization"],
        "fixed_code": (
            "import json\n"
            "import os\n"
            "\n"
            "def load_user_data(filename):\n"
            "    safe_path = os.path.basename(filename)\n"
            "    with open(safe_path, 'r') as f:\n"
            "        return json.load(f)"
        ),
        "test_cases": [],
        "review": {
            "bugs": [],
            "security_issues": [
                {"line": 6, "severity": "high", "description": "pickle.load on untrusted data allows arbitrary code execution"},
                {"line": 5, "severity": "high", "description": "No path validation — path traversal allows reading arbitrary files"},
            ],
            "style_violations": [
                {"line": 4, "severity": "low", "description": "Missing docstring explaining expected file format"},
            ],
        },
    },
    {
        "id": 13,
        "code": (
            "def average(numbers):\n"
            "    return sum(numbers) / len(numbers)"
        ),
        "bug_type": "division by zero",
        "bug_type_aliases": ["empty list not handled", "zerodivisionerror", "missing empty check"],
        "fixed_code": (
            "def average(numbers):\n"
            "    if not numbers:\n"
            "        return 0.0\n"
            "    return sum(numbers) / len(numbers)"
        ),
        "test_cases": [
            ([1, 2, 3], 2.0),
            ([10], 10.0),
            ([0, 0, 0], 0.0),
        ],
        "review": {
            "bugs": [
                {"line": 2, "severity": "high", "description": "ZeroDivisionError when numbers is an empty list"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 1, "severity": "low", "description": "Missing type hint and docstring"},
            ],
        },
    },
    {
        "id": 14,
        "code": (
            "def get_env_secret():\n"
            "    import os\n"
            "    secret = os.getenv('SECRET_KEY', 'hardcoded-secret-1234')\n"
            "    return secret"
        ),
        "bug_type": "hardcoded secret",
        "bug_type_aliases": ["hardcoded credential", "secret in source code", "insecure default"],
        "fixed_code": (
            "def get_env_secret():\n"
            "    import os\n"
            "    secret = os.getenv('SECRET_KEY')\n"
            "    if not secret:\n"
            "        raise EnvironmentError('SECRET_KEY environment variable is not set')\n"
            "    return secret"
        ),
        "test_cases": [],
        "review": {
            "bugs": [],
            "security_issues": [
                {"line": 3, "severity": "high", "description": "Hardcoded fallback secret exposed in source code — never commit credentials"},
            ],
            "style_violations": [
                {"line": 3, "severity": "low", "description": "Silent fallback to default hides misconfiguration — raise an error instead"},
            ],
        },
    },
    {
        "id": 15,
        "code": (
            "def parse_config(config_text):\n"
            "    import json\n"
            "    return eval(config_text)\n"
            "\n"
            "def get_threshold(config_text):\n"
            "    config = parse_config(config_text)\n"
            "    return config.get('threshold', 0)"
        ),
        "bug_type": "eval misuse",
        "bug_type_aliases": ["eval injection", "unsafe eval", "code injection via eval"],
        "fixed_code": (
            "def parse_config(config_text):\n"
            "    import json\n"
            "    data = json.loads(config_text)\n"
            "    if not isinstance(data, dict):\n"
            "        raise ValueError('Config must be a JSON object')\n"
            "    return data\n"
            "\n"
            "def get_threshold(config_text):\n"
            "    config = parse_config(config_text)\n"
            "    return config.get('threshold', 0)"
        ),
        "test_cases": [
            ("{\"threshold\": 5}", 5),
            ("{}", 0),
        ],
        "review": {
            "bugs": [],
            "security_issues": [
                {"line": 3, "severity": "high", "description": "eval on untrusted config_text enables arbitrary code execution"},
            ],
            "style_violations": [
                {"line": 2, "severity": "low", "description": "Import should be at module scope for clarity"},
            ],
        },
    },
    {
        "id": 16,
        "code": (
            "import os\n"
            "\n"
            "def read_user_file(base_dir, filename):\n"
            "    path = os.path.join(base_dir, filename)\n"
            "    with open(path, 'r') as f:\n"
            "        return f.read()"
        ),
        "bug_type": "unsafe file handling",
        "bug_type_aliases": ["path traversal", "unsafe path join", "missing path validation"],
        "fixed_code": (
            "import os\n"
            "\n"
            "def read_user_file(base_dir, filename):\n"
            "    base = os.path.abspath(base_dir)\n"
            "    target = os.path.abspath(os.path.join(base, filename))\n"
            "    if not target.startswith(base + os.sep):\n"
            "        raise ValueError('Invalid filename')\n"
            "    with open(target, 'r') as f:\n"
            "        return f.read()"
        ),
        "test_cases": [],
        "review": {
            "bugs": [],
            "security_issues": [
                {"line": 4, "severity": "high", "description": "User-controlled filename can escape base_dir via path traversal"},
            ],
            "style_violations": [
                {"line": 4, "severity": "low", "description": "Use pathlib for clearer path handling"},
            ],
        },
    },
    {
        "id": 17,
        "code": (
            "import os\n"
            "\n"
            "def ping_host(host):\n"
            "    cmd = f'ping -c 1 {host}'\n"
            "    return os.system(cmd)"
        ),
        "bug_type": "command injection",
        "bug_type_aliases": ["shell injection", "os command injection", "unsanitised command"],
        "fixed_code": (
            "import subprocess\n"
            "\n"
            "def ping_host(host):\n"
            "    if not host.replace('.', '').isdigit():\n"
            "        raise ValueError('Invalid host')\n"
            "    result = subprocess.run(['ping', '-c', '1', host], capture_output=True, text=True)\n"
            "    return result.returncode"
        ),
        "test_cases": [],
        "review": {
            "bugs": [],
            "security_issues": [
                {"line": 4, "severity": "high", "description": "os.system with interpolated host allows command injection"},
            ],
            "style_violations": [
                {"line": 4, "severity": "low", "description": "Prefer subprocess.run with shell=False"},
            ],
        },
    },
    {
        "id": 18,
        "code": (
            "import sqlite3\n"
            "\n"
            "def get_user(conn, username):\n"
            "    cursor = conn.cursor()\n"
            "    cursor.execute(f\"SELECT id, email FROM users WHERE username = '{username}'\")\n"
            "    return cursor.fetchone()"
        ),
        "bug_type": "sql injection",
        "bug_type_aliases": ["unsanitised sql", "string formatting in sql", "parameterised query missing"],
        "fixed_code": (
            "import sqlite3\n"
            "\n"
            "def get_user(conn, username):\n"
            "    cursor = conn.cursor()\n"
            "    cursor.execute(\"SELECT id, email FROM users WHERE username = ?\", (username,))\n"
            "    return cursor.fetchone()"
        ),
        "test_cases": [],
        "review": {
            "bugs": [],
            "security_issues": [
                {"line": 5, "severity": "high", "description": "String formatting in SQL enables injection of arbitrary queries"},
            ],
            "style_violations": [
                {"line": 4, "severity": "low", "description": "Reuse a cursor or context manager for efficiency"},
            ],
        },
    },
    {
        "id": 19,
        "code": (
            "def average_latency(samples):\n"
            "    total = sum(samples)\n"
            "    return total / len(samples)\n"
            "\n"
            "def report_latency(samples):\n"
            "    avg = average_latency(samples)\n"
            "    return {'avg_ms': round(avg, 2), 'count': len(samples)}"
        ),
        "bug_type": "division by zero",
        "bug_type_aliases": ["zero division error", "missing empty check", "empty list not handled"],
        "fixed_code": (
            "def average_latency(samples):\n"
            "    if not samples:\n"
            "        return 0.0\n"
            "    total = sum(samples)\n"
            "    return total / len(samples)\n"
            "\n"
            "def report_latency(samples):\n"
            "    avg = average_latency(samples)\n"
            "    return {'avg_ms': round(avg, 2), 'count': len(samples)}"
        ),
        "test_cases": [
            ([100, 200, 300], {'avg_ms': 200.0, 'count': 3}),
            ([], {'avg_ms': 0.0, 'count': 0}),
        ],
        "review": {
            "bugs": [
                {"line": 3, "severity": "high", "description": "len(samples) can be zero, causing ZeroDivisionError"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 1, "severity": "low", "description": "Consider documenting expected units (ms)"},
            ],
        },
    },
    {
        "id": 20,
        "code": (
            "def find_account(accounts, account_id):\n"
            "    for acc in accounts:\n"
            "        if acc['id'] == account_id:\n"
            "            return acc\n"
            "    return None\n"
            "\n"
            "def get_account_email(accounts, account_id):\n"
            "    account = find_account(accounts, account_id)\n"
            "    return account['email']"
        ),
        "bug_type": "null pointer dereference",
        "bug_type_aliases": ["none dereference", "missing null check", "typeerror on none"],
        "fixed_code": (
            "def find_account(accounts, account_id):\n"
            "    for acc in accounts:\n"
            "        if acc['id'] == account_id:\n"
            "            return acc\n"
            "    return None\n"
            "\n"
            "def get_account_email(accounts, account_id):\n"
            "    account = find_account(accounts, account_id)\n"
            "    if account is None:\n"
            "        return None\n"
            "    return account['email']"
        ),
        "test_cases": [
            (([{"id": 1, "email": "a@b.com"}], 1), "a@b.com"),
            (([{"id": 1, "email": "a@b.com"}], 2), None),
        ],
        "review": {
            "bugs": [
                {"line": 9, "severity": "high", "description": "account can be None, causing TypeError when indexing"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 8, "severity": "low", "description": "Return a clear error or exception when account is missing"},
            ],
        },
    },
    {
        "id": 21,
        "code": (
            "def has_increasing_pair(values):\n"
            "    for i in range(len(values)):\n"
            "        if values[i + 1] > values[i]:\n"
            "            return True\n"
            "    return False"
        ),
        "bug_type": "index out of range",
        "bug_type_aliases": ["off by one", "range error", "index error"],
        "fixed_code": (
            "def has_increasing_pair(values):\n"
            "    for i in range(len(values) - 1):\n"
            "        if values[i + 1] > values[i]:\n"
            "            return True\n"
            "    return False"
        ),
        "test_cases": [
            ([1, 2], True),
            ([2, 1], False),
            ([1], False),
            ([], False),
        ],
        "review": {
            "bugs": [
                {"line": 3, "severity": "high", "description": "values[i + 1] reads past end on last iteration"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 2, "severity": "low", "description": "Handle empty lists explicitly for clarity"},
            ],
        },
    },
    {
        "id": 22,
        "code": (
            "def get_page(items, page, size):\n"
            "    start = page * size\n"
            "    end = (page + 1) * size\n"
            "    page_items = []\n"
            "    for i in range(start, end + 1):\n"
            "        if i < len(items):\n"
            "            page_items.append(items[i])\n"
            "    return page_items"
        ),
        "bug_type": "incorrect loop bounds",
        "bug_type_aliases": ["off by one", "inclusive range", "loop bound error"],
        "fixed_code": (
            "def get_page(items, page, size):\n"
            "    start = page * size\n"
            "    end = (page + 1) * size\n"
            "    page_items = []\n"
            "    for i in range(start, end):\n"
            "        if i < len(items):\n"
            "            page_items.append(items[i])\n"
            "    return page_items"
        ),
        "test_cases": [
            ((list(range(10)), 0, 5), [0, 1, 2, 3, 4]),
            ((list(range(10)), 1, 5), [5, 6, 7, 8, 9]),
        ],
        "review": {
            "bugs": [
                {"line": 5, "severity": "medium", "description": "range(start, end + 1) includes an extra element"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 4, "severity": "low", "description": "Use slicing for simpler pagination"},
            ],
        },
    },
    {
        "id": 23,
        "code": (
            "def is_active(user):\n"
            "    return user.get('status') == 'active'\n"
            "\n"
            "def count_active(users):\n"
            "    total = 0\n"
            "    for user in users:\n"
            "        if is_active(user):\n"
            "            total == total + 1\n"
            "    return total"
        ),
        "bug_type": "wrong operator",
        "bug_type_aliases": ["assignment vs comparison", "== instead of =", "comparison instead of assignment"],
        "fixed_code": (
            "def is_active(user):\n"
            "    return user.get('status') == 'active'\n"
            "\n"
            "def count_active(users):\n"
            "    total = 0\n"
            "    for user in users:\n"
            "        if is_active(user):\n"
            "            total = total + 1\n"
            "    return total"
        ),
        "test_cases": [
            (([{"status": "active"}, {"status": "inactive"}],), 1),
            (([{"status": "inactive"}],), 0),
        ],
        "review": {
            "bugs": [
                {"line": 8, "severity": "high", "description": "total == total + 1 compares instead of updating"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 1, "severity": "low", "description": "Consider typing for user schema"},
            ],
        },
    },
    {
        "id": 24,
        "code": (
            "def total_price(order):\n"
            "    total = 0.0\n"
            "    for item in order['items']:\n"
            "        total += order['price']\n"
            "    return total"
        ),
        "bug_type": "wrong variable used",
        "bug_type_aliases": ["uses wrong variable", "wrong field referenced", "logic bug"],
        "fixed_code": (
            "def total_price(order):\n"
            "    total = 0.0\n"
            "    for item in order['items']:\n"
            "        total += item['price']\n"
            "    return total"
        ),
        "test_cases": [
            (({"items": [{"price": 2.5}, {"price": 7.5}], "price": 100.0},), 10.0),
        ],
        "review": {
            "bugs": [
                {"line": 4, "severity": "high", "description": "Uses order['price'] instead of item['price'] per line item"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 1, "severity": "low", "description": "Consider validating item structure before access"},
            ],
        },
    },
    {
        "id": 25,
        "code": (
            "def append_audit_log(path, line):\n"
            "    log = open(path, 'a')\n"
            "    log.write(line + '\\n')\n"
            "    return True"
        ),
        "bug_type": "resource leak",
        "bug_type_aliases": ["file not closed", "unclosed file handle", "missing context manager"],
        "fixed_code": (
            "def append_audit_log(path, line):\n"
            "    with open(path, 'a') as log:\n"
            "        log.write(line + '\\n')\n"
            "    return True"
        ),
        "test_cases": [],
        "review": {
            "bugs": [
                {"line": 2, "severity": "medium", "description": "File handle is never closed, leaking resources"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 2, "severity": "low", "description": "Use with-statement for file IO"},
            ],
        },
    },
    {
        "id": 26,
        "code": (
            "_cached_items = []\n"
            "\n"
            "def remember_recent(items, max_size=100):\n"
            "    for item in items:\n"
            "        _cached_items.append(item)\n"
            "    return len(_cached_items)"
        ),
        "bug_type": "memory leak",
        "bug_type_aliases": ["unbounded cache", "growing list", "no cache eviction"],
        "fixed_code": (
            "_cached_items = []\n"
            "\n"
            "def remember_recent(items, max_size=100):\n"
            "    for item in items:\n"
            "        _cached_items.append(item)\n"
            "    if len(_cached_items) > max_size:\n"
            "        _cached_items[:] = _cached_items[-max_size:]\n"
            "    return len(_cached_items)"
        ),
        "test_cases": [
            (([1, 2, 3, 4], 3), 3),
            (([5], 3), 3),
        ],
        "review": {
            "bugs": [
                {"line": 5, "severity": "medium", "description": "Cache grows without bound and never evicts items"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 1, "severity": "low", "description": "Global mutable state makes testing harder"},
            ],
        },
    },
    {
        "id": 27,
        "code": (
            "import os\n"
            "\n"
            "def delete_user_file(base_dir, filename):\n"
            "    path = os.path.join(base_dir, filename)\n"
            "    os.remove(path)\n"
            "    return True"
        ),
        "bug_type": "unsafe file handling",
        "bug_type_aliases": ["path traversal", "unsafe delete", "missing path validation"],
        "fixed_code": (
            "import os\n"
            "\n"
            "def delete_user_file(base_dir, filename):\n"
            "    base = os.path.abspath(base_dir)\n"
            "    target = os.path.abspath(os.path.join(base, filename))\n"
            "    if not target.startswith(base + os.sep):\n"
            "        raise ValueError('Invalid filename')\n"
            "    os.remove(target)\n"
            "    return True"
        ),
        "test_cases": [],
        "review": {
            "bugs": [],
            "security_issues": [
                {"line": 4, "severity": "high", "description": "User-controlled filename can delete arbitrary files"},
            ],
            "style_violations": [
                {"line": 5, "severity": "low", "description": "Consider checking file existence before remove"},
            ],
        },
    },
    {
        "id": 28,
        "code": (
            "def can_access(user, required_flags):\n"
            "    flags = user.get('flags', 0)\n"
            "    return (flags | required_flags) == required_flags"
        ),
        "bug_type": "wrong operator",
        "bug_type_aliases": ["bitwise or instead of and", "operator misuse", "logic error"],
        "fixed_code": (
            "def can_access(user, required_flags):\n"
            "    flags = user.get('flags', 0)\n"
            "    return (flags & required_flags) == required_flags"
        ),
        "test_cases": [
            (({"flags": 0b010}, 0b010), True),
            (({"flags": 0b010}, 0b011), False),
        ],
        "review": {
            "bugs": [
                {"line": 3, "severity": "medium", "description": "Bitwise OR always sets bits, granting access incorrectly"},
            ],
            "security_issues": [
                {"line": 3, "severity": "medium", "description": "Permission check can be bypassed due to wrong operator"},
            ],
            "style_violations": [],
        },
    },
    {
        "id": 29,
        "code": (
            "def sum_matrix(matrix):\n"
            "    total = 0\n"
            "    for r in range(len(matrix) + 1):\n"
            "        for c in range(len(matrix[0])):\n"
            "            total += matrix[r][c]\n"
            "    return total"
        ),
        "bug_type": "index out of range",
        "bug_type_aliases": ["off by one", "range error", "index error"],
        "fixed_code": (
            "def sum_matrix(matrix):\n"
            "    total = 0\n"
            "    for r in range(len(matrix)):\n"
            "        for c in range(len(matrix[0])):\n"
            "            total += matrix[r][c]\n"
            "    return total"
        ),
        "test_cases": [
            (([[1, 2], [3, 4]],), 10),
            (([[5]],), 5),
        ],
        "review": {
            "bugs": [
                {"line": 3, "severity": "high", "description": "range(len(matrix) + 1) reads past last row"},
            ],
            "security_issues": [],
            "style_violations": [
                {"line": 4, "severity": "low", "description": "Assumes rectangular matrix without validation"},
            ],
        },
    },
]
