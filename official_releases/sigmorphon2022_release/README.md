# Camel Morph SIGMORPHON 2022

This section guides you through the process of inspecting, making use of, and replicating the results obtained for the SIGMORPHON 2022 Camel Morph paper[^1]. Firstly, all the data can be obtained or viewed as described in the [Data](https://github.com/CAMeL-Lab/camel_morph#data) section in the main [README](../README.md) of the repository. However, all the data and code (including relevant Camel Tools modules) required to replicate the paper results are already contained in the standalone `./sigmorphon2022_release` directory. Furthermore, the generated DBs can only be read by the Camel Tools modules included in the latter directory, and not using the official Camel Tools release. To replicate the paper results, follow the below instructions. For a fuller picture of all configurations, see the [Instructions](https://github.com/CAMeL-Lab/camel_morph#instructions) section in the main [README](../README.md) of the repository.

## Installation

1. Clone (download) this repository and unzip in a directory of your choice.
2. Make sure that you are running **Python 3.8** or **Python 3.9** (this release was tested on these two versions, but it is likely that it will work on other versions).
3. Run the following command to install all needed libraries: `pip install -r requirements.txt`.
4. Run all commands/scripts from the `sigmorphon2022_release` directory.

## Data

[![License](https://mirrors.creativecommons.org/presskit/buttons/80x15/svg/by.svg)](https://creativecommons.org/licenses/by/4.0/)

The data used to compile a database is available in `csv` format (the way it was at submission time) in the following [folder](https://github.com/CAMeL-Lab/camel_morph/tree/main/sigmorphon2022_release/data).

The data is also available for viewing from the Google Sheets interface using the following links, although, column width is not adjustable (you can download the sheet and open it in a personal spreadsheet as a workaround).

- [MSA Verbs Specifications (Camera Ready)](https://docs.google.com/spreadsheets/d/1v9idxctnr6IsqG4c7bHs7lGx7GzbnTa2s4ghQCmLoPY/edit#gid=524706154)
- [EGY Verbs Specifications (Camera Ready)](https://docs.google.com/spreadsheets/d/1OCqHIdeZpm9BNa-BiC7Xy6bAT_wkLnhuvKdo7X3-RtE/edit#gid=424095452)

### Data License

The data files accessed through the below links are licensed under a [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/). For code license, see [License](#license).

## Modern Standard Arabic (MSA) Results

To generate the MSA verbs database, the results of which were described in the paper[^1], run the following two commands from the main repository directory to output the resulting DB (`msa_cam_ready_sigmorphon2022_v1.0.db`) into the `sigmorphon2022_release/databases/camel-morph-msa` directory:

    >> cd sigmorphon2022_release
    >> python db_maker.py -config_file config.json -config_name msa_cam_ready_sigmorphon2022 

## Egyptian Arabic (EGY) Results

To generate the EGY verbs database, the results of which were described in the paper[^1], run the following two commands from the main repository directory to output the resulting DB (`egy_cam_ready_sigmorphon2022_v1.0.db`) into the `sigmorphon2022_release/databases/camel-morph-egy` directory:

    >> cd sigmorphon2022_release
    >> python db_maker.py -config_file config.json -config_name egy_cam_ready_sigmorphon2022

## Dummy Example

The example described in Figure 2 of the paper [^1] was recreated for initiation purposes under the configuration name `msa_example_sigmorphon2022`. The DB for it can be generated in a similar fashion as for the DBs above.

## Analysis and Generation

In order to use the generated DB for analysis or generation, follow the same instructions provided in the examples at the following links. Note that the Camel Tools modules included in the `sigmorphon2022_release` directory are required to be used instead of the official release. As long as all code is ran from inside the latter directory, then all behavior should be similar to actually using the official library:

- [Analysis](https://camel-tools.readthedocs.io/en/latest/api/morphology/analyzer.html)
  - [Disambiguation](https://camel-tools.readthedocs.io/en/latest/api/disambig/mle.html) (in-context analysis)
- [Generation](https://camel-tools.readthedocs.io/en/latest/api/morphology/generator.html)

[^1]: Nizar Habash, Reham Marzouk, Christian Khairallah, and Salam Khalifa. 2022. [Morphotactic Modeling in an Open-source Multi-dialectal Arabic Morphological Analyzer and Generator](https://aclanthology.org/2022.sigmorphon-1.10/). In Proceedings of the 19th SIGMORPHON Workshop on Computational Research in Phonetics, Phonology, and Morphology, pages 92–102, Seattle, Washington. Association for Computational Linguistics.
