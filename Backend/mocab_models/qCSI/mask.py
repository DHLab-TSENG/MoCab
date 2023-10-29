from mocab_models.qCSI.mask_module import ConcreteMaskMart
from mocab_models.qCSI.mask_module import ConcreteMaskType
from mocab_models.qCSI.mask_module import ConcreteRegexSearch
import pandas as pd

unit_type = ("o2_flow_rate", "fio2")
mask_type = ("Simple Mask", "Nasal Cannula", "Non-rebreathing Mask", "Tracheal Mask", "V-Mask", "High Flow Mask")


def mask():
    global mask_mart
    mask_mart = ConcreteMaskMart()

    # Create a new Observer called simple_mask
    simple_mask = ConcreteMaskType(mask_type[0])
    mask_mart.attach(simple_mask)

    # two regex contains in the simple mask_module
    simple_mask_flow_rate = ConcreteRegexSearch(unit_type[0], [
        r"mask.*%? (\d{1,2}).*l",
        r"s-m.*?(\d{1,2}) *l",
        r"sm.*?(\d{1,2})l\/min",
        r"s'm.*?(\d{1,2})l\/ *min",
        r"simpo.*mask.*?(\d{1,2}) *?l\/min",
        r"s\/m.*(\d{1,2})(l ?(\/min)?[^a-z]|liter|lpm)",
        r"mask.*?(\d{1,2} *?l)",
        r"(^[0-9]*$)"
    ])
    simple_mask_fio2 = ConcreteRegexSearch(unit_type[1], [
        r"mask.*?(\d{2,3}) *(%)",
    ])
    simple_mask.attach_search_regex(simple_mask_flow_rate, simple_mask_fio2)

    # Nasal Cannula
    nasal_cannula = ConcreteMaskType(mask_type[1])
    mask_mart.attach(nasal_cannula, 1)
    nasal_cannula_flow_rate = ConcreteRegexSearch(unit_type[0], [
        r"nasal.*?(\d{1,2}) *([l1]\/m|lpm)"
        r"cannula.*?(\d{1,2}).{0,2}l ?(\/min)?",
        r"nasal.*(\d{1,2})[ _]{0,3}[^a-z]*(l ?(\/min)?[^a-z]|liter|lpm)",
        r"n\/c.*?(\d{1,2})l\/min",
        r"nc.*(\d{1,2}?l)\/min",
    ])
    nasal_cannula_fio2 = ConcreteRegexSearch(unit_type[1], [
        r"nasal.*(\d{2,3}) *(%)"
    ])
    nasal_cannula.attach_search_regex(nasal_cannula_flow_rate, nasal_cannula_fio2)

    # Non-Rebreathing Mask
    non_rebreathing_mask = ConcreteMaskType(mask_type[2])
    mask_mart.attach(non_rebreathing_mask, 1)
    non_rebreathing_mask_flow_rate = ConcreteRegexSearch(unit_type[0], [
        r"non-?rebreath.*(\d{1,2}) *(l\/m|lpm)",
    ])
    non_rebreathing_mask_fio2 = ConcreteRegexSearch(unit_type[1], [
        r"non-?rebreath.*?(\d{2,3}).*%",
    ])
    non_rebreathing_mask.attach_search_regex(non_rebreathing_mask_flow_rate, non_rebreathing_mask_fio2)

    # Tracheal Mask
    tracheal_mask = ConcreteMaskType(mask_type[3], )
    mask_mart.attach(tracheal_mask, 2)
    tracheal_mask_flow_rate = ConcreteRegexSearch(unit_type[0], [
        r"tracheal.*?(\d{1,2}) ?l"
    ])
    tracheal_mask_fio2 = ConcreteRegexSearch(unit_type[1], [
        r"tracheal.*(\d{2,3}) *(%)",
    ])
    tracheal_mask.attach_search_regex(tracheal_mask_flow_rate, tracheal_mask_fio2)

    return mask_mart


mask_mart = globals()['mask']()

if __name__ == '__main__':
    # here put your inpatient treatment text
    # mask()
    with open("./csv/A053_急診處置.csv", newline='') as csv_file:
        df = pd.read_csv(csv_file, encoding="utf-8")
        for row in df.iterrows():
            row = row[1]
            txt = str(row.treatment_mining)
            # txt = "MASK 10L/MIN->N/C 3L/MIN"

            result = mask_mart.treatment_mining(txt)
            if result:
                print('txt= {}, \nresult= {}'.format(txt, result))
                print("---------------------------")
    print("Done")
