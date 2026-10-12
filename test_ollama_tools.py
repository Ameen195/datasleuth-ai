
from langchain_ollama import ChatOllama
from langchain_core.tools import tool


@tool
def inspect_dataset() -> str:
    """Return a short description of the synthetic transaction dataset."""
    return (
        "The dataset has 100 rows. "
        "Known issues include duplicate transaction IDs, "
        "one missing date, and one negative amount."
    )


def main() -> None:
    model = ChatOllama(
        model="qwen3.5:4b",
        temperature=0,
    )

    model_with_tools = model.bind_tools([inspect_dataset])

    response = model_with_tools.invoke(
        "Investigate the transaction dataset. "
        "Use the inspect_dataset tool to obtain evidence."
    )

    print("Model response:", response.content)
    print("Requested tool calls:", response.tool_calls)

    if response.tool_calls:
        print("SUCCESS: The model requested a tool call.")
    else:
        print(
            "Tool calling was not demonstrated. "
            "We must resolve this before building the agent."
        )


if __name__ == "__main__":
    main()
