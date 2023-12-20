import json
import json
import argparse

def role_type(string):
    roles = {'U': 'user', 'A': 'assistant', 'S': 'system'}
    return roles.get(string.upper(), string)

class MessageExtractor:
    def __init__(self, role, filename):
        self.role = role
        self.filename = filename
        self.contents = []
        self._load_messages()

    def _load_messages(self):
        try:
            with open(self.filename, 'r') as file:
                for line in file:
                    data = json.loads(line)
                    self.contents.extend([mes["content"] for mes in data["messages"] if mes["role"] == self.role])
        except FileNotFoundError:
            print(f"File not found: {self.filename}")

    def get_message(self, n):
        if n <= len(self.contents):
            return self.contents[n-1]
        else:
            return f"No {self.role} content found at line {n}"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, help="The line number to be extracted.", required=True)
    parser.add_argument("--role", type=role_type, choices=['user', 'assistant', 'system', 'U', 'A', 'S'],
                        help="The role of the message to be extracted. Accepts 'user' (or 'U'), 'assistant' (or 'A'), 'system' (or 'S').",
                        required=True)
    parser.add_argument("--filename", type=str, default="mydata1.jsonl", help="The filename of the data to be processed.")

    args = parser.parse_args()

    extractor = MessageExtractor(args.role, args.filename)
    print(extractor.get_message(args.n))

