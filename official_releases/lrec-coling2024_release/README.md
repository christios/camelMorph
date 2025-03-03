# Camel Morph LREC-COLING 2024

This section guides you through the process of inspecting, making use of, and replicating the results obtained for the LREC-COLING 2024 Camel Morph paper. All the data and code (including relevant Camel Tools modules) required to replicate the paper results are already contained in the standalone `camel_morph/official_releases/lrec-coling2024_release/` directory. Furthermore, the generated DB can be read using the official [Camel Tools](https://github.com/CAMeL-Lab/camel_tools) release, but the evaluation/statistics scripts can only ran using the Camel Tools modules included in the latter directory. To replicate the paper results, follow the below instructions.

## Installation

### For Generating a DB Only

To start working with the Camel Morph environment and compiling Mordern Standard Arabic (MSA) databases:

1. Clone (download) this repository and unzip in a directory of your choice.
2. Make sure that you are running **Python 3.8** or **Python 3.9** (this release was tested on these two versions, but it is likely that it will work on other versions).
3. Run the following command to install all needed libraries: `pip install -r requirements.txt`.
4. Run all commands/scripts from the `lrec-coling2024_release/` directory.

### For Running Evaluation Scripts

To run the evaluation and statistics scripts:

1. Clone (download) a [fork](https://github.com/christios/camel_tools) of the Camel Tools repository.
2. Set the `$CAMEL_TOOLS_PATH` value to the path of the Camel Tools fork repository in the configuration file that you will be using (see [Configuration File Structure](../../README.md/#configuration-file-structure) section).

## Data

[![License](https://mirrors.creativecommons.org/presskit/buttons/80x15/svg/by.svg)](https://creativecommons.org/licenses/by/4.0/)

### Specifications

The data used to compile a database is available in `csv` format (the way it was at submission time) in the [data/](./data/) folder contained in this directory.

The data is also available for viewing from the Google Sheets interface using the following links, although, column width is not adjustable (you can download the sheet and open it in a personal spreadsheet as a workaround):

- [MSA Verbs Specifications (Camera Ready)](https://docs.google.com/spreadsheets/d/1V6TdCM6V5byu9HGCdmVY979MhQ2pyNQdO8XkRx3_n2M/edit#gid=210443809)
- [MSA Nominals and Others Specifications (Camera Ready)](https://docs.google.com/spreadsheets/d/1s3nocf4bAxOsXjcvSMulJr5N9Yq1yUWyy5M6XkJk2_s/edit#gid=898723826)
- [MSA Annex - Wiki Proper Nouns (Camera Ready)](https://docs.google.com/spreadsheets/d/1U_V8wNo5gHokTdxG5HaEaqcgjArgecRLiXEi5kMIlX4/edit#gid=1328530526)

### Database

The database file generated by the DB Maker [code](./camel_morph/db_maker.py) using the above [specifications](#specifications) can be found [here](./databases/camel-morph-msa/).

The files accessed through the above links are licensed under a [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).

## Modern Standard Arabic (MSA) Full System Results

### Generating a DB

To generate the full system MSA database, the results of which were described in the paper, run the following two commands from the main repository directory to output the resulting [DB](./databases/camel-morph-msa/camel_morph_msa_v1.0.db) into the `lrec-coling2024_release/databases/camel-morph-msa` directory. From the main `camel_morph/` folder, run:

    >> cd lrec-coling2024_release
    >> python camel_morph/db_maker.py -config_file config_full_system.json -config_name camel_morph_msa 

**Note: This procedure will take around 45 minutes to 1 hour depending on your hardware.**

To generate the pickle file containing the log probablities assigned to lemmas (and specified via the configuration file), run:

    >> cd lrec-coling2024_release
    >> python camel_morph/sandbox/get_logprob_atb.py -magold <msa_magold_path> -ext camel -output_dir_magold_calima <output_dir> -output_dir_magold_camel <output_dir>

which will generate the logprob pickle file that should be specified in the configuration under the keyword argument `logprob` while building the DB. For this, you will need the ATB data synchronized with a version of SAMA/MADA for `<msa_magold_path>`, which is [here](https://drive.google.com/file/d/1Z8ZGB6Z6cQQoUQvj_2r8m1wWqd7BVWaL/view?usp=drive_link), but not publicly accessible. This will be used to synchronize between Camel lemmas and ATB lemmas, and we need this because we have changed the spelling of many lemmas for better consistency. Also `<output_dir>` should be the directory where the new synchronization (Camel-synchronized and Calima-synchronized ATB MAGOLD) files should be output. These two files will be used in the process by the above script to generate appropriate log probabilities.

### Generating the Paper Statistics

To generate the statistics found in *Table 1* of the paper, run:

    >> cd lrec-coling2024_release
    >> python camel_morph/eval/evaluate_camel_morph_stats.py -config_file config_paper_example.json -config_name <config_name> -no_download -no_build -example_counts

where `config_name` is `msa_EalaY`, `msa_ramaY`, or `msa_safiyr`. In addition to the complex morpheme count, you will get a table of simple morpheme counts.

To generate the statistics found in *Table 2* of the paper, run:

    >> cd lrec-coling2024_release
    >> python camel_morph/eval/evaluate_camel_morph_stats.py -config_file config_full_system.json -config_name camel_morph_msa -msa_baseline_db <calima_msa_db_path> -no_download -no_build

where you would need the `calima-msa-s31_0.4.2.utf8.db` DB file which is stored [here](https://drive.google.com/file/d/1ggbUpaXJ_-jiGhmpGsMRpd9SwM0wZo17/view?usp=drive_link), but which is not publicly accessible because it is under copyrights. If you have this file, then add the following argument to the above command: `-msa_baseline_db /path/to/calima/db`. Otherwise, please contact us.

### Evaluation

To evaluate and get the results presented in the *Evaluation* section of the paper, then run:

    >> cd lrec-coling2024_release
    >> python camel_morph/eval/evaluate_camel_morph.py -eval_mode recall_msa_magold_ldc_dediac_match_no_null -config_file config_full_system.json -msa_config_name camel_morph_msa -pos_or_type <required_pos> -output_dir <report_dir>

where `<required_pos>` should be one of: `verbal`, `noun`, `noun_num`, `noun_quant`, `noun_prop`, `adj`, `adj_comp`, `adj_num`, or `other` (for all other POS); `<report_dir>` is the folder path where you want to output the evaluation report to, e.g., `lrec-coling2024_eval/`. Also, to run this script you would need the Calima-synchronized ATB data for the `-msa_magold_path` argument, which is [here](https://drive.google.com/file/d/1mVWONav2pxIdwBTJQaZovGpUqUIe3eBa/view?usp=drive_link), but also not publicly accessible. If you have this file, then add the following argument to the above command: `-msa_magold_path <msa_magold_path>`. Otherwise, please contact us.

## Analysis and Generation

In order to use the generated DB for analysis or generation, follow the same instructions provided in the examples at the following links:

- [Analysis](https://camel-tools.readthedocs.io/en/latest/api/morphology/analyzer.html)
  - [Disambiguation](https://camel-tools.readthedocs.io/en/latest/api/disambig/mle.html) (in-context analysis)
- [Generation](https://camel-tools.readthedocs.io/en/latest/api/morphology/generator.html)
