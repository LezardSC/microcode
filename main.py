import requests
from client import LocalLLMClient

def main():
    print("Bienvenue dans l'instance de Qwen3.5:9b\n")
    client = LocalLLMClient()

    while True:
        try:
            content = input("Vous: ")

            if content.lower() in ["quit", "exit"]:
                print("\nEnd of conversation.")
                break

            if not content.strip():
                continue

            assistant_reply = client.send_message(content)
            print(f"\nAssistant:\n{assistant_reply}\n")

        except requests.exceptions.RequestException as e:
            print(f"\nNetwork Error: Can't join the API: {e}")
        except  KeyboardInterrupt:
            print("\nEnd of conversation.")
            break

if __name__ == "__main__":
    main()
