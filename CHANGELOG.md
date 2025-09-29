# v0.8.2 (Mon Sep 29 2025)

#### 🐛 Bug Fixes

- [FIX] Log informative error when BIDS table is empty or missing required columns [#549](https://github.com/neurobagel/bagel-cli/pull/549) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.8.1 (Fri Sep 26 2025)

#### 🐛 Bug Fixes

- [FIX] Exit gracefully when `bids2tsv` finds no valid NIfTI files [#546](https://github.com/neurobagel/bagel-cli/pull/546) ([@alyssadai](https://github.com/alyssadai))
- [FIX] Filter `bids2table`-generated table by BIDS supported suffixes [#544](https://github.com/neurobagel/bagel-cli/pull/544) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.8.0 (Thu Sep 11 2025)

#### 💥 Breaking Changes

- [ENH] Releasing changes to data dictionary schema and healthy control handling [#506](https://github.com/neurobagel/bagel-cli/pull/506) ([@alyssadai](https://github.com/alyssadai))
- [ENH] Remove `"Identifies"` key and add `"VariableType"` key to data dictionary schema [#488](https://github.com/neurobagel/bagel-cli/pull/488) ([@alyssadai](https://github.com/alyssadai))
- [ENH] Refactor healthy control parsing [#489](https://github.com/neurobagel/bagel-cli/pull/489) ([@alyssadai](https://github.com/alyssadai))

#### 🐛 Bug Fixes

- [FIX] Add back missing `@context` to `bids` and `derivatives`-generated JSONLDs [#532](https://github.com/neurobagel/bagel-cli/pull/532) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.7.2 (Tue Sep 09 2025)

#### 🔩 Dependency Updates

- [FIX] Pin bids2table version to avoid v2.1.1 bug causing import errors [#529](https://github.com/neurobagel/bagel-cli/pull/529) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.7.1 (Tue Aug 19 2025)

#### 🚀 Enhancements

- [FIX] Remove custom entrypoint that checks for within-container BIDS path [#515](https://github.com/neurobagel/bagel-cli/pull/515) ([@alyssadai](https://github.com/alyssadai))
- [ENH] Warn when only ID columns are annotated, simplify log messages [#514](https://github.com/neurobagel/bagel-cli/pull/514) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.7.0 (Thu Aug 14 2025)

#### 💥 Breaking Changes

- [ENH] Add `bids2tsv` command to convert a BIDS dir into a minimal TSV, and update `bids` command to read from TSV [#481](https://github.com/neurobagel/bagel-cli/pull/481) ([@alyssadai](https://github.com/alyssadai))

#### 🚀 Enhancements

- [ENH] Support custom vocabs for `pheno` via `--config` option & defer errors from resource fetching [#498](https://github.com/neurobagel/bagel-cli/pull/498) ([@alyssadai](https://github.com/alyssadai))
- [MODEL] Add a `pandera` schema for the BIDS metadata table [#503](https://github.com/neurobagel/bagel-cli/pull/503) ([@alyssadai](https://github.com/alyssadai))
- [ENH] More user-friendly error messages for `pheno` command input validation [#508](https://github.com/neurobagel/bagel-cli/pull/508) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.6.0 (Mon Jun 23 2025)

#### 🚀 Enhancements

- [MNT] Set up `bagel` CLI for publishing on PyPi [#460](https://github.com/neurobagel/bagel-cli/pull/460) ([@alyssadai](https://github.com/alyssadai))

#### 🏠 Internal

- [CI] Release the CLI [#465](https://github.com/neurobagel/bagel-cli/pull/465) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.5.0 (Wed Jun 04 2025)

#### 🚀 Enhancements

- [ENH] Rename `"Transformation"` to `"Format"` in data dictionary model [#459](https://github.com/neurobagel/bagel-cli/pull/459) ([@alyssadai](https://github.com/alyssadai))
- [ENH] Split `--bids-dir` into input and host path options [#449](https://github.com/neurobagel/bagel-cli/pull/449) ([@alyssadai](https://github.com/alyssadai) [@rmanaem](https://github.com/rmanaem))

#### Authors: 2

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))
- Arman Jahanpour ([@rmanaem](https://github.com/rmanaem))

---

# v0.4.4 (Tue Apr 08 2025)

#### 🚀 Enhancements

- [REF] Switch to logging for errors and add `--verbosity` option for log level [#446](https://github.com/neurobagel/bagel-cli/pull/446) ([@alyssadai](https://github.com/alyssadai))
- [REF] Switch to logging for warnings and info messages [#444](https://github.com/neurobagel/bagel-cli/pull/444) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.4.3 (Fri Mar 07 2025)

#### 🚀 Enhancements

- [ENH] Support ranged ages with `nb:FromRange` [#437](https://github.com/neurobagel/bagel-cli/pull/437) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.4.2 (Tue Feb 11 2025)

#### 🏠 Internal

- [ENH] Add docker image build for arm64 architecture [#429](https://github.com/neurobagel/bagel-cli/pull/429) ([@rmanaem](https://github.com/rmanaem) [@surchs](https://github.com/surchs))

#### Authors: 2

- Arman Jahanpour ([@rmanaem](https://github.com/rmanaem))
- Sebastian Urchs ([@surchs](https://github.com/surchs))

---

# v0.4.1 (Wed Jan 29 2025)

#### 🐛 Bug Fixes

- [FIX] Disallow empty string/whitespace-only `pheno --name` values [#426](https://github.com/neurobagel/bagel-cli/pull/426) ([@alyssadai](https://github.com/alyssadai))

#### 🏠 Internal

- [MNT] Configure mypy in pre-commit for type checking [#423](https://github.com/neurobagel/bagel-cli/pull/423) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.4.0 (Tue Jan 07 2025)

#### 💥 Breaking Changes

- [MNT] Deprecate Cognitive Atlas vocab namespace & add check for unsupported namespaces [#410](https://github.com/neurobagel/bagel-cli/pull/410) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.3.5 (Wed Dec 11 2024)

#### 🚀 Enhancements

- [ENH] Allow unrecognized pipeline names and versions in processing status file [#401](https://github.com/neurobagel/bagel-cli/pull/401) ([@alyssadai](https://github.com/alyssadai))
- [MNT] Remind about missing value annotation in age parsing error [#402](https://github.com/neurobagel/bagel-cli/pull/402) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.3.4 (Wed Nov 20 2024)

#### 🚀 Enhancements

- [ENH] Load pipeline catalog dynamically and error out when it is empty/not found [#391](https://github.com/neurobagel/bagel-cli/pull/391) ([@surchs](https://github.com/surchs) [@alyssadai](https://github.com/alyssadai))

#### 🏠 Internal

- [REF] Refactor utilities [#385](https://github.com/neurobagel/bagel-cli/pull/385) ([@alyssadai](https://github.com/alyssadai))

#### 🔩 Dependency Updates

- [REF] Upgrade codebase to Pydantic>2 [#389](https://github.com/neurobagel/bagel-cli/pull/389) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 2

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))
- Sebastian Urchs ([@surchs](https://github.com/surchs))

---

# v0.3.3 (Thu Nov 07 2024)

#### 🚀 Enhancements

- [FIX] Package `pipeline-catalog` as data files in CLI installation [#379](https://github.com/neurobagel/bagel-cli/pull/379) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.3.2 (Tue Nov 05 2024)

#### 🚀 Enhancements

- [FIX] Make `pipeline-catalog` submodule available to built Docker image [#373](https://github.com/neurobagel/bagel-cli/pull/373) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.3.1 (Mon Nov 04 2024)

#### 🚀 Enhancements

- [FIX] Add missing `_id` suffix to processing status file column mappings [#370](https://github.com/neurobagel/bagel-cli/pull/370) ([@alyssadai](https://github.com/alyssadai))

#### 📝 Documentation

- [DOC] Move pre-commit setup to README.md [#368](https://github.com/neurobagel/bagel-cli/pull/368) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.3.0 (Thu Oct 24 2024)

#### 💥 Breaking Changes

- [MODEL] Model basic pipeline availability info in imaging session [#347](https://github.com/neurobagel/bagel-cli/pull/347) ([@alyssadai](https://github.com/alyssadai))

#### 🚀 Enhancements

- [ENH] Add derivatives command and `pipeline-catalog` submodule [#349](https://github.com/neurobagel/bagel-cli/pull/349) ([@alyssadai](https://github.com/alyssadai))
- [REF] Rename Neurobagel-created session to `ses-unnamed` [#358](https://github.com/neurobagel/bagel-cli/pull/358) ([@alyssadai](https://github.com/alyssadai))
- [ENH] More user-friendly handling of input decoding/reading errors [#337](https://github.com/neurobagel/bagel-cli/pull/337) ([@alyssadai](https://github.com/alyssadai))

#### 🏠 Internal

- [INF] Add script to generate `nb_vocab.ttl` [#360](https://github.com/neurobagel/bagel-cli/pull/360) ([@alyssadai](https://github.com/alyssadai))
- [MNT] Removed build docker nightly workflow file [#348](https://github.com/neurobagel/bagel-cli/pull/348) ([@rmanaem](https://github.com/rmanaem))

#### 📝 Documentation

- [DOC] Remove usage instructions & update development environment section in README [#365](https://github.com/neurobagel/bagel-cli/pull/365) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 2

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))
- Arman Jahanpour ([@rmanaem](https://github.com/rmanaem))

---

# v0.2.2 (Fri Jul 19 2024)

### Release Notes

#### [CI] Release the CLI ([#330](https://github.com/neurobagel/bagel-cli/pull/330))

This release introduces short option names for CLI commands and fixes a bug that prevented hyphens in column names from being parsed.

---

#### 🚀 Enhancements

- [CI] Release the CLI [#330](https://github.com/neurobagel/bagel-cli/pull/330) ([@alyssadai](https://github.com/alyssadai))
- [ENH] Update help text and add short CLI options [#316](https://github.com/neurobagel/bagel-cli/pull/316) ([@alyssadai](https://github.com/alyssadai))

#### 🐛 Bug Fixes

- [FIX] Handle dashes (/any chars that are not python variable valid) in column names [#313](https://github.com/neurobagel/bagel-cli/pull/313) ([@alyssadai](https://github.com/alyssadai))

#### 📝 Documentation

- [DOC] Note case sensitivity of subject IDs in `bids` IDs check error [#317](https://github.com/neurobagel/bagel-cli/pull/317) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 1

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))

---

# v0.2.2 (Fri Jul 19 2024)

### Release Notes

#### [MNT] Release the CLI ([#291](https://github.com/neurobagel/bagel-cli/pull/291))

We have updated the Neurobagel data model to allow users to specify phenotypic information at the session level (https://github.com/neurobagel/planning/issues/83). This release updates the CLI so you can create `.jsonld` files according to the new data model.

---

#### 🚀 Enhancements

- [ENH] Update help text and add short CLI options [#316](https://github.com/neurobagel/bagel-cli/pull/316) ([@alyssadai](https://github.com/alyssadai))
- [MNT] Release the CLI [#291](https://github.com/neurobagel/bagel-cli/pull/291) ([@alyssadai](https://github.com/alyssadai) [@surchs](https://github.com/surchs))

#### 🐛 Bug Fixes

- [FIX] Handle dashes (/any chars that are not python variable valid) in column names [#313](https://github.com/neurobagel/bagel-cli/pull/313) ([@alyssadai](https://github.com/alyssadai))

#### 📝 Documentation

- [DOC] Note case sensitivity of subject IDs in `bids` IDs check error [#317](https://github.com/neurobagel/bagel-cli/pull/317) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 2

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))
- Sebastian Urchs ([@surchs](https://github.com/surchs))

---

# v0.2.2 (Thu Apr 11 2024)

### Release Notes

#### [MNT] Release the CLI ([#291](https://github.com/neurobagel/bagel-cli/pull/291))

We have updated the Neurobagel data model to allow users to specify phenotypic information at the session level (https://github.com/neurobagel/planning/issues/83). This release updates the CLI so you can create `.jsonld` files according to the new data model.

---

#### 🚀 Enhancements

- [MNT] Release the CLI [#291](https://github.com/neurobagel/bagel-cli/pull/291) ([@alyssadai](https://github.com/alyssadai) [@surchs](https://github.com/surchs))

#### Authors: 2

- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))
- Sebastian Urchs ([@surchs](https://github.com/surchs))

---

# v0.2.1 (Mon Jan 08 2024)

#### 🐛 Bug Fix

- [FIX] Use different reviewer token in release.yaml [#268](https://github.com/neurobagel/bagel-cli/pull/268) ([@alyssadai](https://github.com/alyssadai))
- [ENH] Handle multi-column attribute annotations [#264](https://github.com/neurobagel/bagel-cli/pull/264) ([@alyssadai](https://github.com/alyssadai))
- Bump bids-examples from `1a000d6` to `eff47f1` [#265](https://github.com/neurobagel/bagel-cli/pull/265) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- [CI] Allow auto to push on protected branch [#261](https://github.com/neurobagel/bagel-cli/pull/261) ([@alyssadai](https://github.com/alyssadai))
- Bump bids-examples from `b6e5234` to `1a000d6` [#256](https://github.com/neurobagel/bagel-cli/pull/256) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- [CI] Switch to parallel build config for coveralls [#263](https://github.com/neurobagel/bagel-cli/pull/263) ([@alyssadai](https://github.com/alyssadai))
- [MODEL] Handle phenotypic inputs with no session column in the TSV [#260](https://github.com/neurobagel/bagel-cli/pull/260) ([@alyssadai](https://github.com/alyssadai))
- [MNT] Stop pre-commit from pushing to PR branches [#253](https://github.com/neurobagel/bagel-cli/pull/253) ([@surchs](https://github.com/surchs))

#### Authors: 3

- [@dependabot[bot]](https://github.com/dependabot[bot])
- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))
- Sebastian Urchs ([@surchs](https://github.com/surchs))

---

# v0.2.0 (Thu Dec 14 2023)

#### 🚀 Enhancement

- [MODEL] Update data model to include longitudinal pheno data when sessions exist in TSV [#250](https://github.com/neurobagel/bagel-cli/pull/250) ([@alyssadai](https://github.com/alyssadai) [@surchs](https://github.com/surchs) [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))

#### 🐛 Bug Fix

- [CI] give auto-release permissions to launch build [#255](https://github.com/neurobagel/bagel-cli/pull/255) ([@surchs](https://github.com/surchs))
- [CI] Add Codecov to test workflow [#254](https://github.com/neurobagel/bagel-cli/pull/254) ([@alyssadai](https://github.com/alyssadai))
- [TST] Added a test to ensure correct labelling of phenotypic sessions [#251](https://github.com/neurobagel/bagel-cli/pull/251) ([@sam-gregz](https://github.com/sam-gregz))
- Bump actions/setup-python from 4 to 5 [#246](https://github.com/neurobagel/bagel-cli/pull/246) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- [CI] Update .autorc to release with release label [#248](https://github.com/neurobagel/bagel-cli/pull/248) ([@alyssadai](https://github.com/alyssadai) [@surchs](https://github.com/surchs) [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot]))
- Bump actions/stale from 8 to 9 [#245](https://github.com/neurobagel/bagel-cli/pull/245) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- Bump neurobagel_examples from `f1b00e5` to `94282f1` [#249](https://github.com/neurobagel/bagel-cli/pull/249) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- [MNT] Update the neurobagel examples [#247](https://github.com/neurobagel/bagel-cli/pull/247) ([@surchs](https://github.com/surchs))
- Delete .github/workflows/add_pr2project.yml [#244](https://github.com/neurobagel/bagel-cli/pull/244) ([@surchs](https://github.com/surchs))

#### Authors: 5

- [@dependabot[bot]](https://github.com/dependabot[bot])
- [@pre-commit-ci[bot]](https://github.com/pre-commit-ci[bot])
- [@sam-gregz](https://github.com/sam-gregz)
- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))
- Sebastian Urchs ([@surchs](https://github.com/surchs))

---

# v0.1.3 (Tue Dec 12 2023)

#### 🐛 Bug Fix

- Bump actions/stale from 8 to 9 [#245](https://github.com/neurobagel/bagel-cli/pull/245) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- Bump neurobagel_examples from `f1b00e5` to `94282f1` [#249](https://github.com/neurobagel/bagel-cli/pull/249) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- [MNT] Update the neurobagel examples [#247](https://github.com/neurobagel/bagel-cli/pull/247) ([@surchs](https://github.com/surchs))
- Delete .github/workflows/add_pr2project.yml [#244](https://github.com/neurobagel/bagel-cli/pull/244) ([@surchs](https://github.com/surchs))

#### Authors: 2

- [@dependabot[bot]](https://github.com/dependabot[bot])
- Sebastian Urchs ([@surchs](https://github.com/surchs))

---

# v0.1.5 (Mon Dec 11 2023)

#### 🐛 Bug Fix

- Bump neurobagel_examples from `f1b00e5` to `94282f1` [#249](https://github.com/neurobagel/bagel-cli/pull/249) ([@dependabot[bot]](https://github.com/dependabot[bot]))

#### Authors: 1

- [@dependabot[bot]](https://github.com/dependabot[bot])

---

# v0.1.3 (Mon Dec 11 2023)

#### 🐛 Bug Fix

- [MNT] Update the neurobagel examples [#247](https://github.com/neurobagel/bagel-cli/pull/247) ([@surchs](https://github.com/surchs))
- Delete .github/workflows/add_pr2project.yml [#244](https://github.com/neurobagel/bagel-cli/pull/244) ([@surchs](https://github.com/surchs))

#### Authors: 1

- Sebastian Urchs ([@surchs](https://github.com/surchs))

---

# v0.1.3 (Sun Dec 10 2023)

#### 🐛 Bug Fix

- Delete .github/workflows/add_pr2project.yml [#244](https://github.com/neurobagel/bagel-cli/pull/244) ([@surchs](https://github.com/surchs))

#### Authors: 1

- Sebastian Urchs ([@surchs](https://github.com/surchs))

---

# v0.1.2 (Thu Dec 07 2023)

#### 🐛 Bug Fix

- [CI] Added `release` workflow [#243](https://github.com/neurobagel/bagel-cli/pull/243) ([@rmanaem](https://github.com/rmanaem))
- [DOC] Added link to official docs [#237](https://github.com/neurobagel/bagel-cli/pull/237) ([@surchs](https://github.com/surchs))
- Bump bids-examples from `e073115` to `b6e5234` [#232](https://github.com/neurobagel/bagel-cli/pull/232) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- [ENH] Change assessment tool availability heuristic to `any()` [#234](https://github.com/neurobagel/bagel-cli/pull/234) ([@alyssadai](https://github.com/alyssadai))

#### 🏠 Internal

- [CI] Update image tag for default build + add wf to build on release [#242](https://github.com/neurobagel/bagel-cli/pull/242) ([@alyssadai](https://github.com/alyssadai))

#### Authors: 4

- [@dependabot[bot]](https://github.com/dependabot[bot])
- Alyssa Dai ([@alyssadai](https://github.com/alyssadai))
- Arman Jahanpour ([@rmanaem](https://github.com/rmanaem))
- Sebastian Urchs ([@surchs](https://github.com/surchs))
