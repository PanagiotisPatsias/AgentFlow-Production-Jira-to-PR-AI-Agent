from typing import List 

def parse_ticket_description(text: str) -> tuple[str, list[str]]:

    criteria : list[str] =[]

    idx = text.find("Acceptance Criteria:")
    if idx == -1:
        return text.strip(), criteria
    rest = text[idx:]

    rest = rest.removeprefix("Acceptance Criteria:")
    lines = rest.split("\n")

    for line in lines:
        line = line.strip()

        if line.startswith("-"):
            line = line[1:].strip()

        if line:
            criteria.append(line)
    

    return text[:idx].strip(), criteria
        