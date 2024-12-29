import os
import argparse
from pathlib import Path
from datetime import datetime

import pandas
from dotenv import load_dotenv
from national._959.endorse.extract import main as extract


def transform(*foo):
    """Module that transform"""
    return {}


def match(*foo):
    """Module that matches"""
    return {}


FILENAME = f"_NA_AFRA_"


def save_records(
    records: dict[int, dict[str, str]],
    filename: str,
    filepath: Path,
    *additional_info,
):

    filepath.mkdir(exist_ok=True)
    timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d-%H%M%S-%f")

    df = pandas.DataFrame.from_dict(records, orient="index")
    df.to_csv(
        filepath
        / (
            f"{filename}_{'-'.join(map(str, additional_info))}"
            f"{'-' if additional_info else ''}{timestamp}.csv"
        ),
        index=False,
    )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-d",
        "--export_path",
        type=Path,
        required=True,
        help="filepath of the directory where files are exported to",
    )

    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="read extracted or transformed file",
    )

    parser.add_argument(
        "-y",
        "--year",
        type=str,
        help="Year(s) of the endorsements",
    )

    parser.add_argument(
        "-hp",
        "--html_path",
        type=Path,
        help="filepath to HTML directory",
    )

    parser.add_argument(
        "-e",
        "--extract",
        action="store_true",
        help="to extract only",
    )

    parser.add_argument(
        "-t",
        "--transform",
        action="store_true",
        help="to transform only",
    )

    parser.add_argument(
        "-m",
        "--match",
        action="store_true",
        help="to match only",
    )

    args = parser.parse_args()

    load_dotenv()

    vsdb_conn_info = {
        "host": os.getenv("VSDB_HOST"),
        "dbname": os.getenv("VSDB_DBNAME"),
        "port": os.getenv("VSDB_PORT"),
        "user": os.getenv("VSDB_USER"),
        "password": os.getenv("VSDB_PASSWORD"),
    }

    if not any((args.extract, args.transform, args.match)):

        records_extracted = extract(
            FILENAME + "Endorsements", args.export_path, args.html_path
        )
        save_records(
            records_extracted,
            FILENAME + "Endorsements-Extract",
            args.export_path / "EXTRACT_FILES",
        )

        # records_transformed = transform(records_extracted)
        # save_records(
        #     records_transformed,
        #     FILENAME + "Endorsements-Transformed",
        #     args.export_path / "TRANSFORMED_FILES",
        # )

        # records_matched, records_election_candidates = match(
        #     records_transformed, vsdb_conn_info
        # )

        # save_records(
        #     records_matched,
        #     FILENAME + "Endorsements-Matched",
        #     args.export_path / "MATCHED_FILES",
        # )

        # save_records(
        #     records_election_candidates,
        #     FILENAME + "VSDB-Candidates",
        #     args.export_path / "QUERY_FILES",
        # )

    elif args.extract and not (any((args.transform, args.match))):

        records_extracted = extract(
            FILENAME + "Endorsements", args.export_path, args.html_path
        )
        save_records(
            records_extracted,
            FILENAME + "Endorsements-Extract",
            args.export_path / "EXTRACT_FILES",
        )

    elif args.transform and not (any((args.extract, args.match))):
        if not args.file:
            parser.print_help()
            parser.error("Please specify the filepath of the spreadsheet.")

        df_extracted = pandas.read_csv(args.file)
        records_extracted = df_extracted.to_dict(orient="index")

        records_transformed = transform(records_extracted)
        save_records(
            records_transformed,
            FILENAME + "Endorsements-Transformed",
            args.export_path / "TRANSFORMED_FILES",
        )

    elif args.match and not any((args.extract, args.transform)):
        if not args.file:
            parser.print_help()
            parser.error("Please specify the filepath of the spreadsheet.")

        df_transformed = pandas.read_csv(
            args.file, na_values="nan", keep_default_na=False
        )
        records_transformed = df_transformed.to_dict(orient="index")

        records_matched, records_election_candidates = match(
            records_transformed, vsdb_conn_info
        )

        save_records(
            records_matched,
            FILENAME + "Endorsements-Matched",
            args.export_path / "MATCHED_FILES",
        )

        save_records(
            records_election_candidates,
            FILENAME + "VSDB-Candidates",
            args.export_path / "QUERY_FILES",
        )


if __name__ == "__main__":
    main()
