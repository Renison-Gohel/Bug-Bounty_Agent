from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.runnables.base import coerce_to_runnable

print("--- Debugging RunnablePassthrough ---")

def mock_func(x):
    return "test"

try:
    print("1. Testing coerce_to_runnable with lambda")
    l = lambda x: mock_func(x)
    print(f"Lambda: {l}")
    r = coerce_to_runnable(l)
    print(f"Coerced: {r}")

    print("2. Testing RunnableParallel with lambda")
    rp = RunnableParallel(agent_scratchpad=l)
    print(f"RunnableParallel: {rp}")

    print("3. Testing RunnablePassthrough.assign with lambda")
    assign = RunnablePassthrough.assign(agent_scratchpad=l)
    print(f"RunnablePassthrough.assign: {assign}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
