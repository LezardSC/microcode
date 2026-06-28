import requests
from client import LocalLLMClient

def main():
    client = LocalLLMClient(sys_prompt_path='system_prompt.txt')

    while True:
        try:
            content = input("Vous: ")

            if content.lower() in ["quit", "exit"]:
                print("\nEnd of conversation.")
                break

            if not content.strip():
                continue

            assistant_reply = client.send_message(content)

            print(f"\n\nAssistant:\n")
            for text_fragment in assistant_reply:
                print(text_fragment, end="", flush=True)
            print()

        except requests.exceptions.RequestException as e:
            print(f"\nNetwork Error: Can't join the API: {e}")
        except  KeyboardInterrupt:
            print("\nEnd of conversation.")
            break

if __name__ == "__main__":
    main()
