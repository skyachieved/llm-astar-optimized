"""Make Figs. 1-3 with their default settings.

  python -m llmastar.figures [--model llama-3-8b-instruct]
"""
import argparse

from llmastar.figures import fig1_search, fig2_examples, fig3_scalability


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="llama-3-8b-instruct")
    args = p.parse_args(argv)
    for figure in (fig1_search, fig2_examples, fig3_scalability):
        figure.main(["--model", args.model])


if __name__ == "__main__":
    main()
