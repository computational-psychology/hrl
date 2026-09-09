import data_management
import pandas as pd

CONTEXTS = (
    "plain",
    "light",
    "light",
    "dark",
    "dark",
    "plain",
    "plain",
    "light",
    "plain",
    "dark",
)
RS = (1.67, 1.29, 0.46, 1.67, 0.82, 0.46, 0.31, 0.63, 0.11, 1.67)


def generate_session(Nrepeats=1):
    for i in range(Nrepeats):
        block = generate_block()
        block_id = f"{i}"

        # Save to file
        filepath = data_management.design_filepath(block_id)
        block.to_csv(filepath)


def generate_block():
    # Combine all variables
    trials = [(r, context) for r, context in zip(RS, CONTEXTS)]

    # Convert to dataframe
    block = pd.DataFrame(trials, columns=["r", "context"])

    # Shuffle trial order
    # block = block.reindex(np.random.permutation(block.index))
    # block.reset_index(drop=True, inplace=True)
    block.index.name = "trial"

    return block


if __name__ == "__main__":
    Nrepeats = int(input("N repeats?"))
    generate_session(Nrepeats=Nrepeats)
