# Data Dictionary

**Dataset:** UCI 697, Predict Students' Dropout and Academic Success. **Generated:** 2026-09-09 17:30 UTC by
`python -m ssn data profile`. Do not edit the generated tables; hand-written notes go in the notes block.

**Unit of analysis:** one student enrollment record (UCI: "Each instance is a student").
**Rows × columns observed:** 4424 × 37.

Availability classes: `enrollment` (known at enrollment), `first_semester` (end of semester 1),
`second_semester` (prohibited for the deployed model), `outcome` (the target), `ambiguous`
(timing undocumented; excluded by default, see research R-05). Roles: `feature`, `sensitive`
(aggregate fairness auditing only, never a model input), `target`.

## Columns

| Column | UCI name | Availability | Role | Type | Documented values / range | Observed | Missing | Encoding verified | Description |
|---|---|---|---|---|---|---|---|---|---|
| Marital status | Marital Status | enrollment | sensitive | categorical | 1=single; 2=married; 3=widower; 4=divorced; 5=facto union; 6=legally separated | 6 distinct codes | 0 | yes | 1 – single 2 – married 3 – widower 4 – divorced 5 – facto union 6 – legally separated |
| Application mode |  | enrollment | feature | categorical | 1=1st phase - general contingent; 2=Ordinance No. 612/93; 5=1st phase - special contingent (Azores Island); 7=Holders of other higher courses; 10=Ordinance No. 854-B/99; 15=International student (bachelor) … (+12 more) | 18 distinct codes | 0 | yes | 1 - 1st phase - general contingent 2 - Ordinance No. 612/93 5 - 1st phase - special contingent (Azores Island) 7 - Holders of other higher courses 10 - Ordinance No. 854-B/99 15 - International student (bachelor) 16 - 1st phase - special contingent (Madeira Island) 17 - 2nd phase - general contingent 18 - 3rd phase - general contingent 26 - Ordinance No. 533-A/99, item b2) (Different Plan) 27 - Ordinance No. 533-A/99, item b3 (Other Institution) 39 - Over 23 years old 42 - Transfer 43 - Change of course 44 - Technological specialization diploma holders 51 - Change of institution/course 53 - Short cycle diploma holders 57 - Change of institution/course (International) |
| Application order |  | enrollment | feature | numeric | [0, 9] | 0 – 9 | 0 | n/a | Application order (between 0 - first choice; and 9 last choice) |
| Course |  | enrollment | feature | categorical | 33=Biofuel Production Technologies; 171=Animation and Multimedia Design; 8014=Social Service (evening attendance); 9003=Agronomy; 9070=Communication Design; 9085=Veterinary Nursing … (+11 more) | 17 distinct codes | 0 | yes | 33 - Biofuel Production Technologies 171 - Animation and Multimedia Design 8014 - Social Service (evening attendance) 9003 - Agronomy 9070 - Communication Design 9085 - Veterinary Nursing 9119 - Informatics Engineering 9130 - Equinculture 9147 - Management 9238 - Social Service 9254 - Tourism 9500 - Nursing 9556 - Oral Hygiene 9670 - Advertising and Marketing Management 9773 - Journalism and Communication 9853 - Basic Education 9991 - Management (evening attendance) |
| Daytime/evening attendance |  | enrollment | feature | binary | 1=daytime; 0=evening | 2 distinct codes | 0 | yes | 1 – daytime 0 - evening |
| Previous qualification |  | enrollment | feature | categorical | 1=Secondary education; 2=Higher education - bachelor's degree; 3=Higher education - degree; 4=Higher education - master's; 5=Higher education - doctorate; 6=Frequency of higher education … (+11 more) | 17 distinct codes | 0 | yes | 1 - Secondary education 2 - Higher education - bachelor's degree 3 - Higher education - degree 4 - Higher education - master's 5 - Higher education - doctorate 6 - Frequency of higher education 9 - 12th year of schooling - not completed 10 - 11th year of schooling - not completed 12 - Other - 11th year of schooling 14 - 10th year of schooling 15 - 10th year of schooling - not completed 19 - Basic education 3rd cycle (9th/10th/11th year) or equiv. 38 - Basic education 2nd cycle (6th/7th/8th year) or equiv. 39 - Technological specialization course 40 - Higher education - degree (1st cycle) 42 - Professional higher technical course 43 - Higher education - master (2nd cycle) |
| Previous qualification (grade) |  | enrollment | feature | numeric | [0, 200] | 95 – 190 | 0 | n/a | Grade of previous qualification (between 0 and 200) |
| Nacionality |  | enrollment | sensitive | categorical | 1=Portuguese; 2=German; 6=Spanish; 11=Italian; 13=Dutch; 14=English … (+15 more) | 21 distinct codes | 0 | yes | 1 - Portuguese; 2 - German; 6 - Spanish; 11 - Italian; 13 - Dutch; 14 - English; 17 - Lithuanian; 21 - Angolan; 22 - Cape Verdean; 24 - Guinean; 25 - Mozambican; 26 - Santomean; 32 - Turkish; 41 - Brazilian; 62 - Romanian; 100 - Moldova (Republic of); 101 - Mexican; 103 - Ukrainian; 105 - Russian; 108 - Cuban; 109 - Colombian |
| Mother's qualification |  | enrollment | feature | categorical | 1=Secondary Education - 12th Year of Schooling or Eq.; 2=Higher Education - Bachelor's Degree; 3=Higher Education - Degree; 4=Higher Education - Master's; 5=Higher Education - Doctorate; 6=Frequency of Higher Education … (+23 more) | 29 distinct codes | 0 | yes | 1 - Secondary Education - 12th Year of Schooling or Eq. 2 - Higher Education - Bachelor's Degree 3 - Higher Education - Degree 4 - Higher Education - Master's 5 - Higher Education - Doctorate 6 - Frequency of Higher Education 9 - 12th Year of Schooling - Not Completed 10 - 11th Year of Schooling - Not Completed 11 - 7th Year (Old) 12 - Other - 11th Year of Schooling 14 - 10th Year of Schooling 18 - General commerce course 19 - Basic Education 3rd Cycle (9th/10th/11th Year) or Equiv. 22 - Technical-professional course 26 - 7th year of schooling 27 - 2nd cycle of the general high school course 29 - 9th Year of Schooling - Not Completed 30 - 8th year of schooling 34 - Unknown 35 - Can't read or write 36 - Can read without having a 4th year of schooling 37 - Basic education 1st cycle (4th/5th year) or equiv. 38 - Basic Education 2nd Cycle (6th/7th/8th Year) or Equiv. 39 - Technological specialization course 40 - Higher education - degree (1st cycle) 41 - Specialized higher studies course 42 - Professional higher technical course 43 - Higher Education - Master (2nd cycle) 44 - Higher Education - Doctorate (3rd cycle) |
| Father's qualification |  | enrollment | feature | categorical | 1=Secondary Education - 12th Year of Schooling or Eq.; 2=Higher Education - Bachelor's Degree; 3=Higher Education - Degree; 4=Higher Education - Master's; 5=Higher Education - Doctorate; 6=Frequency of Higher Education … (+28 more) | 34 distinct codes | 0 | yes | 1 - Secondary Education - 12th Year of Schooling or Eq. 2 - Higher Education - Bachelor's Degree 3 - Higher Education - Degree 4 - Higher Education - Master's 5 - Higher Education - Doctorate 6 - Frequency of Higher Education 9 - 12th Year of Schooling - Not Completed 10 - 11th Year of Schooling - Not Completed 11 - 7th Year (Old) 12 - Other - 11th Year of Schooling 13 - 2nd year complementary high school course 14 - 10th Year of Schooling 18 - General commerce course 19 - Basic Education 3rd Cycle (9th/10th/11th Year) or Equiv. 20 - Complementary High School Course 22 - Technical-professional course 25 - Complementary High School Course - not concluded 26 - 7th year of schooling 27 - 2nd cycle of the general high school course 29 - 9th Year of Schooling - Not Completed 30 - 8th year of schooling 31 - General Course of Administration and Commerce 33 - Supplementary Accounting and Administration 34 - Unknown 35 - Can't read or write 36 - Can read without having a 4th year of schooling 37 - Basic education 1st cycle (4th/5th year) or equiv. 38 - Basic Education 2nd Cycle (6th/7th/8th Year) or Equiv. 39 - Technological specialization course 40 - Higher education - degree (1st cycle) 41 - Specialized higher studies course 42 - Professional higher technical course 43 - Higher Education - Master (2nd cycle) 44 - Higher Education - Doctorate (3rd cycle) |
| Mother's occupation |  | enrollment | feature | categorical | 0=Student; 1=Representatives of the Legislative Power and Executive Bodies, Directors, Directors and Executive Managers; 2=Specialists in Intellectual and Scientific Activities; 3=Intermediate Level Technicians and Professions; 4=Administrative staff; 5=Personal Services, Security and Safety Workers and Sellers … (+26 more) | 32 distinct codes | 0 | yes | 0 - Student 1 - Representatives of the Legislative Power and Executive Bodies, Directors, Directors and Executive Managers 2 - Specialists in Intellectual and Scientific Activities 3 - Intermediate Level Technicians and Professions 4 - Administrative staff 5 - Personal Services, Security and Safety Workers and Sellers 6 - Farmers and Skilled Workers in Agriculture, Fisheries and Forestry 7 - Skilled Workers in Industry, Construction and Craftsmen 8 - Installation and Machine Operators and Assembly Workers 9 - Unskilled Workers 10 - Armed Forces Professions 90 - Other Situation 99 - (blank) 122 - Health professionals 123 - teachers 125 - Specialists in information and communication technologies (ICT) 131 - Intermediate level science and engineering technicians and professions 132 - Technicians and professionals, of intermediate level of health 134 - Intermediate level technicians from legal, social, sports, cultural and similar services 141 - Office workers, secretaries in general and data processing operators 143 - Data, accounting, statistical, financial services and registry-related operators 144 - Other administrative support staff 151 - personal service workers 152 - sellers 153 - Personal care workers and the like 171 - Skilled construction workers and the like, except electricians 173 - Skilled workers in printing, precision instrument manufacturing, jewelers, artisans and the like 175 - Workers in food processing, woodworking, clothing and other industries and crafts 191 - cleaning workers 192 - Unskilled workers in agriculture, animal production, fisheries and forestry 193 - Unskilled workers in extractive industry, construction, manufacturing and transport 194 - Meal preparation assistants |
| Father's occupation |  | enrollment | feature | categorical | 0=Student; 1=Representatives of the Legislative Power and Executive Bodies, Directors, Directors and Executive Managers; 2=Specialists in Intellectual and Scientific Activities; 3=Intermediate Level Technicians and Professions; 4=Administrative staff; 5=Personal Services, Security and Safety Workers and Sellers … (+40 more) | 46 distinct codes | 0 | yes | 0 - Student 1 - Representatives of the Legislative Power and Executive Bodies, Directors, Directors and Executive Managers 2 - Specialists in Intellectual and Scientific Activities 3 - Intermediate Level Technicians and Professions 4 - Administrative staff 5 - Personal Services, Security and Safety Workers and Sellers 6 - Farmers and Skilled Workers in Agriculture, Fisheries and Forestry 7 - Skilled Workers in Industry, Construction and Craftsmen 8 - Installation and Machine Operators and Assembly Workers 9 - Unskilled Workers 10 - Armed Forces Professions 90 - Other Situation 99 - (blank) 101 - Armed Forces Officers 102 - Armed Forces Sergeants 103 - Other Armed Forces personnel 112 - Directors of administrative and commercial services 114 - Hotel, catering, trade and other services directors 121 - Specialists in the physical sciences, mathematics, engineering and related techniques 122 - Health professionals 123 - teachers 124 - Specialists in finance, accounting, administrative organization, public and commercial relations 131 - Intermediate level science and engineering technicians and professions 132 - Technicians and professionals, of intermediate level of health 134 - Intermediate level technicians from legal, social, sports, cultural and similar services 135 - Information and communication technology technicians 141 - Office workers, secretaries in general and data processing operators 143 - Data, accounting, statistical, financial services and registry-related operators 144 - Other administrative support staff 151 - personal service workers 152 - sellers 153 - Personal care workers and the like 154 - Protection and security services personnel 161 - Market-oriented farmers and skilled agricultural and animal production workers 163 - Farmers, livestock keepers, fishermen, hunters and gatherers, subsistence 171 - Skilled construction workers and the like, except electricians 172 - Skilled workers in metallurgy, metalworking and similar 174 - Skilled workers in electricity and electronics 175 - Workers in food processing, woodworking, clothing and other industries and crafts 181 - Fixed plant and machine operators 182 - assembly workers 183 - Vehicle drivers and mobile equipment operators 192 - Unskilled workers in agriculture, animal production, fisheries and forestry 193 - Unskilled workers in extractive industry, construction, manufacturing and transport 194 - Meal preparation assistants 195 - Street vendors (except food) and street service providers |
| Admission grade |  | enrollment | feature | numeric | [0, 200] | 95 – 190 | 0 | n/a | Admission grade (between 0 and 200) |
| Displaced |  | enrollment | feature | binary | 1=yes; 0=no | 2 distinct codes | 0 | yes | 1 – yes 0 – no |
| Educational special needs |  | enrollment | sensitive | binary | 1=yes; 0=no | 2 distinct codes | 0 | yes | 1 – yes 0 – no |
| Debtor |  | ambiguous | feature | binary | 1=yes; 0=no | 2 distinct codes | 0 | yes | 1 – yes 0 – no |
| Tuition fees up to date |  | ambiguous | feature | binary | 1=yes; 0=no | 2 distinct codes | 0 | yes | 1 – yes 0 – no |
| Gender |  | enrollment | sensitive | binary | 1=male; 0=female | 2 distinct codes | 0 | yes | 1 – male 0 – female |
| Scholarship holder |  | ambiguous | feature | binary | 1=yes; 0=no | 2 distinct codes | 0 | yes | 1 – yes 0 – no |
| Age at enrollment |  | enrollment | sensitive | numeric |  | 17 – 70 | 0 | n/a | Age of studend at enrollment |
| International |  | enrollment | sensitive | binary | 1=yes; 0=no | 2 distinct codes | 0 | yes | 1 – yes 0 – no |
| Curricular units 1st sem (credited) |  | first_semester | feature | numeric |  | 0 – 20 | 0 | n/a | Number of curricular units credited in the 1st semester |
| Curricular units 1st sem (enrolled) |  | first_semester | feature | numeric |  | 0 – 26 | 0 | n/a | Number of curricular units enrolled in the 1st semester |
| Curricular units 1st sem (evaluations) |  | first_semester | feature | numeric |  | 0 – 45 | 0 | n/a | Number of evaluations to curricular units in the 1st semester |
| Curricular units 1st sem (approved) |  | first_semester | feature | numeric |  | 0 – 26 | 0 | n/a | Number of curricular units approved in the 1st semester |
| Curricular units 1st sem (grade) |  | first_semester | feature | numeric | [0, 20] | 0 – 18.88 | 0 | n/a | Grade average in the 1st semester (between 0 and 20) |
| Curricular units 1st sem (without evaluations) |  | first_semester | feature | numeric |  | 0 – 12 | 0 | n/a | Number of curricular units without evalutions in the 1st semester |
| Curricular units 2nd sem (credited) |  | second_semester | feature | numeric |  | 0 – 19 | 0 | n/a | Number of curricular units credited in the 2nd semester |
| Curricular units 2nd sem (enrolled) |  | second_semester | feature | numeric |  | 0 – 23 | 0 | n/a | Number of curricular units enrolled in the 2nd semester |
| Curricular units 2nd sem (evaluations) |  | second_semester | feature | numeric |  | 0 – 33 | 0 | n/a | Number of evaluations to curricular units in the 2nd semester |
| Curricular units 2nd sem (approved) |  | second_semester | feature | numeric |  | 0 – 20 | 0 | n/a | Number of curricular units approved in the 2nd semester |
| Curricular units 2nd sem (grade) |  | second_semester | feature | numeric | [0, 20] | 0 – 18.57 | 0 | n/a | Grade average in the 2nd semester (between 0 and 20) |
| Curricular units 2nd sem (without evaluations) |  | second_semester | feature | numeric |  | 0 – 12 | 0 | n/a | Number of curricular units without evalutions in the 1st semester |
| Unemployment rate |  | enrollment | feature | numeric |  | 7.6 – 16.2 | 0 | n/a | Unemployment rate (%) |
| Inflation rate |  | enrollment | feature | numeric |  | -0.8 – 3.7 | 0 | n/a | Inflation rate (%) |
| GDP |  | enrollment | feature | numeric |  | -4.06 – 3.51 | 0 | n/a | GDP |
| Target |  | outcome | target | categorical |  | 3 distinct codes | 0 | n/a | Target. The problem is formulated as a three category classification task (dropout, enrolled, and graduate) at the end of the normal duration of the course |

## Engineered features

_None yet (Milestone 3)._

## Encoding verification

Codes come from the UCI variables table (API `https://archive.ics.uci.edu/api/dataset?id=697`,
retrieved 2026-09-10; see data/README.md).
"Encoding verified: yes" means every observed code appears in the documentation. Observed counts are
computed from the data.

### Marital status

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | single | 3919 |
| 2 | married | 379 |
| 3 | widower | 4 |
| 4 | divorced | 91 |
| 5 | facto union | 25 |
| 6 | legally separated | 6 |
### Application mode

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | 1st phase - general contingent | 1708 |
| 2 | Ordinance No. 612/93 | 3 |
| 5 | 1st phase - special contingent (Azores Island) | 16 |
| 7 | Holders of other higher courses | 139 |
| 10 | Ordinance No. 854-B/99 | 10 |
| 15 | International student (bachelor) | 30 |
| 16 | 1st phase - special contingent (Madeira Island) | 38 |
| 17 | 2nd phase - general contingent | 872 |
| 18 | 3rd phase - general contingent | 124 |
| 26 | Ordinance No. 533-A/99, item b2) (Different Plan) | 1 |
| 27 | Ordinance No. 533-A/99, item b3 (Other Institution) | 1 |
| 39 | Over 23 years old | 785 |
| 42 | Transfer | 77 |
| 43 | Change of course | 312 |
| 44 | Technological specialization diploma holders | 213 |
| 51 | Change of institution/course | 59 |
| 53 | Short cycle diploma holders | 35 |
| 57 | Change of institution/course (International) | 1 |
### Course

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 33 | Biofuel Production Technologies | 12 |
| 171 | Animation and Multimedia Design | 215 |
| 8014 | Social Service (evening attendance) | 215 |
| 9003 | Agronomy | 210 |
| 9070 | Communication Design | 226 |
| 9085 | Veterinary Nursing | 337 |
| 9119 | Informatics Engineering | 170 |
| 9130 | Equinculture | 141 |
| 9147 | Management | 380 |
| 9238 | Social Service | 355 |
| 9254 | Tourism | 252 |
| 9500 | Nursing | 766 |
| 9556 | Oral Hygiene | 86 |
| 9670 | Advertising and Marketing Management | 268 |
| 9773 | Journalism and Communication | 331 |
| 9853 | Basic Education | 192 |
| 9991 | Management (evening attendance) | 268 |
### Daytime/evening attendance

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | daytime | 3941 |
| 0 | evening | 483 |
### Previous qualification

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | Secondary education | 3717 |
| 2 | Higher education - bachelor's degree | 23 |
| 3 | Higher education - degree | 126 |
| 4 | Higher education - master's | 8 |
| 5 | Higher education - doctorate | 1 |
| 6 | Frequency of higher education | 16 |
| 9 | 12th year of schooling - not completed | 11 |
| 10 | 11th year of schooling - not completed | 4 |
| 12 | Other - 11th year of schooling | 45 |
| 14 | 10th year of schooling | 1 |
| 15 | 10th year of schooling - not completed | 2 |
| 19 | Basic education 3rd cycle (9th/10th/11th year) or equiv. | 162 |
| 38 | Basic education 2nd cycle (6th/7th/8th year) or equiv. | 7 |
| 39 | Technological specialization course | 219 |
| 40 | Higher education - degree (1st cycle) | 40 |
| 42 | Professional higher technical course | 36 |
| 43 | Higher education - master (2nd cycle) | 6 |
### Nacionality

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | Portuguese | 4314 |
| 2 | German | 2 |
| 6 | Spanish | 13 |
| 11 | Italian | 3 |
| 13 | Dutch | 1 |
| 14 | English | 1 |
| 17 | Lithuanian | 1 |
| 21 | Angolan | 2 |
| 22 | Cape Verdean | 13 |
| 24 | Guinean | 5 |
| 25 | Mozambican | 2 |
| 26 | Santomean | 14 |
| 32 | Turkish | 1 |
| 41 | Brazilian | 38 |
| 62 | Romanian | 2 |
| 100 | Moldova (Republic of) | 3 |
| 101 | Mexican | 2 |
| 103 | Ukrainian | 3 |
| 105 | Russian | 2 |
| 108 | Cuban | 1 |
| 109 | Colombian | 1 |
### Mother's qualification

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | Secondary Education - 12th Year of Schooling or Eq. | 1069 |
| 2 | Higher Education - Bachelor's Degree | 83 |
| 3 | Higher Education - Degree | 438 |
| 4 | Higher Education - Master's | 49 |
| 5 | Higher Education - Doctorate | 21 |
| 6 | Frequency of Higher Education | 4 |
| 9 | 12th Year of Schooling - Not Completed | 8 |
| 10 | 11th Year of Schooling - Not Completed | 3 |
| 11 | 7th Year (Old) | 3 |
| 12 | Other - 11th Year of Schooling | 42 |
| 14 | 10th Year of Schooling | 2 |
| 18 | General commerce course | 1 |
| 19 | Basic Education 3rd Cycle (9th/10th/11th Year) or Equiv. | 953 |
| 22 | Technical-professional course | 1 |
| 26 | 7th year of schooling | 1 |
| 27 | 2nd cycle of the general high school course | 1 |
| 29 | 9th Year of Schooling - Not Completed | 3 |
| 30 | 8th year of schooling | 3 |
| 34 | Unknown | 130 |
| 35 | Can't read or write | 3 |
| 36 | Can read without having a 4th year of schooling | 3 |
| 37 | Basic education 1st cycle (4th/5th year) or equiv. | 1009 |
| 38 | Basic Education 2nd Cycle (6th/7th/8th Year) or Equiv. | 562 |
| 39 | Technological specialization course | 8 |
| 40 | Higher education - degree (1st cycle) | 9 |
| 41 | Specialized higher studies course | 6 |
| 42 | Professional higher technical course | 4 |
| 43 | Higher Education - Master (2nd cycle) | 4 |
| 44 | Higher Education - Doctorate (3rd cycle) | 1 |
### Father's qualification

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | Secondary Education - 12th Year of Schooling or Eq. | 904 |
| 2 | Higher Education - Bachelor's Degree | 68 |
| 3 | Higher Education - Degree | 282 |
| 4 | Higher Education - Master's | 39 |
| 5 | Higher Education - Doctorate | 18 |
| 6 | Frequency of Higher Education | 2 |
| 9 | 12th Year of Schooling - Not Completed | 5 |
| 10 | 11th Year of Schooling - Not Completed | 2 |
| 11 | 7th Year (Old) | 10 |
| 12 | Other - 11th Year of Schooling | 38 |
| 13 | 2nd year complementary high school course | 1 |
| 14 | 10th Year of Schooling | 4 |
| 18 | General commerce course | 1 |
| 19 | Basic Education 3rd Cycle (9th/10th/11th Year) or Equiv. | 968 |
| 20 | Complementary High School Course | 1 |
| 22 | Technical-professional course | 4 |
| 25 | Complementary High School Course - not concluded | 1 |
| 26 | 7th year of schooling | 2 |
| 27 | 2nd cycle of the general high school course | 1 |
| 29 | 9th Year of Schooling - Not Completed | 3 |
| 30 | 8th year of schooling | 4 |
| 31 | General Course of Administration and Commerce | 1 |
| 33 | Supplementary Accounting and Administration | 1 |
| 34 | Unknown | 112 |
| 35 | Can't read or write | 2 |
| 36 | Can read without having a 4th year of schooling | 8 |
| 37 | Basic education 1st cycle (4th/5th year) or equiv. | 1209 |
| 38 | Basic Education 2nd Cycle (6th/7th/8th Year) or Equiv. | 702 |
| 39 | Technological specialization course | 20 |
| 40 | Higher education - degree (1st cycle) | 5 |
| 41 | Specialized higher studies course | 2 |
| 42 | Professional higher technical course | 1 |
| 43 | Higher Education - Master (2nd cycle) | 2 |
| 44 | Higher Education - Doctorate (3rd cycle) | 1 |
### Mother's occupation

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 0 | Student | 144 |
| 1 | Representatives of the Legislative Power and Executive Bodies, Directors, Directors and Executive Managers | 102 |
| 2 | Specialists in Intellectual and Scientific Activities | 318 |
| 3 | Intermediate Level Technicians and Professions | 351 |
| 4 | Administrative staff | 817 |
| 5 | Personal Services, Security and Safety Workers and Sellers | 530 |
| 6 | Farmers and Skilled Workers in Agriculture, Fisheries and Forestry | 91 |
| 7 | Skilled Workers in Industry, Construction and Craftsmen | 272 |
| 8 | Installation and Machine Operators and Assembly Workers | 36 |
| 9 | Unskilled Workers | 1577 |
| 10 | Armed Forces Professions | 4 |
| 90 | Other Situation | 70 |
| 99 | (blank) | 17 |
| 122 | Health professionals | 2 |
| 123 | teachers | 7 |
| 125 | Specialists in information and communication technologies (ICT) | 1 |
| 131 | Intermediate level science and engineering technicians and professions | 1 |
| 132 | Technicians and professionals, of intermediate level of health | 3 |
| 134 | Intermediate level technicians from legal, social, sports, cultural and similar services | 4 |
| 141 | Office workers, secretaries in general and data processing operators | 8 |
| 143 | Data, accounting, statistical, financial services and registry-related operators | 3 |
| 144 | Other administrative support staff | 6 |
| 151 | personal service workers | 3 |
| 152 | sellers | 2 |
| 153 | Personal care workers and the like | 2 |
| 171 | Skilled construction workers and the like, except electricians | 1 |
| 173 | Skilled workers in printing, precision instrument manufacturing, jewelers, artisans and the like | 1 |
| 175 | Workers in food processing, woodworking, clothing and other industries and crafts | 5 |
| 191 | cleaning workers | 26 |
| 192 | Unskilled workers in agriculture, animal production, fisheries and forestry | 5 |
| 193 | Unskilled workers in extractive industry, construction, manufacturing and transport | 4 |
| 194 | Meal preparation assistants | 11 |
### Father's occupation

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 0 | Student | 128 |
| 1 | Representatives of the Legislative Power and Executive Bodies, Directors, Directors and Executive Managers | 134 |
| 2 | Specialists in Intellectual and Scientific Activities | 197 |
| 3 | Intermediate Level Technicians and Professions | 384 |
| 4 | Administrative staff | 386 |
| 5 | Personal Services, Security and Safety Workers and Sellers | 516 |
| 6 | Farmers and Skilled Workers in Agriculture, Fisheries and Forestry | 242 |
| 7 | Skilled Workers in Industry, Construction and Craftsmen | 666 |
| 8 | Installation and Machine Operators and Assembly Workers | 318 |
| 9 | Unskilled Workers | 1010 |
| 10 | Armed Forces Professions | 266 |
| 90 | Other Situation | 65 |
| 99 | (blank) | 19 |
| 101 | Armed Forces Officers | 1 |
| 102 | Armed Forces Sergeants | 2 |
| 103 | Other Armed Forces personnel | 4 |
| 112 | Directors of administrative and commercial services | 2 |
| 114 | Hotel, catering, trade and other services directors | 1 |
| 121 | Specialists in the physical sciences, mathematics, engineering and related techniques | 1 |
| 122 | Health professionals | 2 |
| 123 | teachers | 3 |
| 124 | Specialists in finance, accounting, administrative organization, public and commercial relations | 1 |
| 131 | Intermediate level science and engineering technicians and professions | 1 |
| 132 | Technicians and professionals, of intermediate level of health | 1 |
| 134 | Intermediate level technicians from legal, social, sports, cultural and similar services | 1 |
| 135 | Information and communication technology technicians | 3 |
| 141 | Office workers, secretaries in general and data processing operators | 1 |
| 143 | Data, accounting, statistical, financial services and registry-related operators | 1 |
| 144 | Other administrative support staff | 8 |
| 151 | personal service workers | 2 |
| 152 | sellers | 3 |
| 153 | Personal care workers and the like | 1 |
| 154 | Protection and security services personnel | 1 |
| 161 | Market-oriented farmers and skilled agricultural and animal production workers | 1 |
| 163 | Farmers, livestock keepers, fishermen, hunters and gatherers, subsistence | 5 |
| 171 | Skilled construction workers and the like, except electricians | 8 |
| 172 | Skilled workers in metallurgy, metalworking and similar | 2 |
| 174 | Skilled workers in electricity and electronics | 1 |
| 175 | Workers in food processing, woodworking, clothing and other industries and crafts | 4 |
| 181 | Fixed plant and machine operators | 3 |
| 182 | assembly workers | 2 |
| 183 | Vehicle drivers and mobile equipment operators | 3 |
| 192 | Unskilled workers in agriculture, animal production, fisheries and forestry | 6 |
| 193 | Unskilled workers in extractive industry, construction, manufacturing and transport | 15 |
| 194 | Meal preparation assistants | 2 |
| 195 | Street vendors (except food) and street service providers | 1 |
### Displaced

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | yes | 2426 |
| 0 | no | 1998 |
### Educational special needs

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | yes | 51 |
| 0 | no | 4373 |
### Debtor

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | yes | 503 |
| 0 | no | 3921 |
### Tuition fees up to date

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | yes | 3896 |
| 0 | no | 528 |
### Gender

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | male | 1556 |
| 0 | female | 2868 |
### Scholarship holder

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | yes | 1099 |
| 0 | no | 3325 |
### International

Source: UCI variables table (api/dataset?id=697, retrieved 2026-09-10)

| Code | Label | Observed count |
|---|---|---|
| 1 | yes | 110 |
| 0 | no | 4314 |

<!-- BEGIN NOTES -->
_Add hand-written notes here; this block survives regeneration._
<!-- END NOTES -->
