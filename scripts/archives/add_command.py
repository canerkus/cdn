import argparse
import json
import os
from pathlib import Path

from rich.console import Console
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm


def update_parser(parser: argparse.ArgumentParser):
    parser.description = "Add new archive to the CDN"
    parser.add_argument("variant", help="archive variant", choices=["evm", "substrate"])
    parser.set_defaults(func=_run)


def _run(parsed_args):
    console = Console()
    registry_name = Prompt.ask("Registry name")
    hr_name = Prompt.ask("Human readable name")
    data_source_id = Prompt.ask("Data source identifier")
    entry = {}
    match parsed_args.variant:
        case "evm":
            chain_id = Prompt.ask("Chain ID", default="null")
            chain_kind = Prompt.ask("Kind", default="unknown", choices=["unknown", "mainnet", "testnet"])
            datasource_data = []
            if Confirm.ask("Datasource supports receipts?", default=True):
                datasource_data.append("receipts")
            if Confirm.ask("Datasource supports traces?", default=False):
                datasource_data.append("traces")
            if Confirm.ask("Datasource supports statediffs?", default=False):
                datasource_data.append("statediffs")
            support_tier = int(Prompt.ask("Support tier", default="3", choices=["1", "2", "3"]))
            entry = {
                "chainId": int(chain_id) if chain_id.isdecimal() else None,
                "chainKind": chain_kind,
                "chainName": hr_name,
                "network": registry_name,
                "providers": [
                    {
                        "dataSourceData": datasource_data,
                        "dataSourceUrl": f"https://v2.archive.subsquid.io/network/{data_source_id}",
                        "provider": "subsquid",
                        "release": "ArrowSquid",
                        "supportTier": support_tier,
                    }
                ],
            }
        case "substrate":
            chain_ss58_prefix = Prompt.ask("Chain SS58 Prefix", default="null")
            genesis_hash = Prompt.ask("Genesis hash", default="")
            entry = {
                "chainName": hr_name,
                "chainSS58Prefix": (
                    int(chain_ss58_prefix) if chain_ss58_prefix.isdecimal() else None
                ),
                "genesis_hash": genesis_hash,
                "network": registry_name,
                "providers": [
                    {
                        "dataSourceData": [],
                        "dataSourceUrl": f"https://v2.archive.subsquid.io/network/{data_source_id}",
                        "provider": "subsquid",
                        "release": "ArrowSquid",
                    }
                ],
            }
        case _:
            raise ValueError("Invalid archive variant")
    syntax = Syntax(
        json.dumps(entry, indent=2), "json", theme="monokai", line_numbers=True
    )
    console.print(
        f"\nFollowing entry will be added to 'src/archives/{parsed_args.variant}.json':"
    )
    console.print(syntax)
    confirm = Confirm.ask("Ok?", default=True)
    if confirm:
        root_p = Path(os.path.realpath(__file__)).parent.parent.parent
        with open(root_p / f"src/archives/{parsed_args.variant}.json") as f:
            archives = json.load(f)
        archives["archives"].append(entry)
        archives["archives"] = sorted(archives["archives"], key=lambda x: x["network"])
        with open(root_p / f"src/archives/{parsed_args.variant}.json", "w") as f:
            json.dump(archives, f, indent=2)
        console.print("Done!")
    else:
        console.print("Abort!")
