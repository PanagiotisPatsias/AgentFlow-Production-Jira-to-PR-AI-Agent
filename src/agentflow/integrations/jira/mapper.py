from typing import Any
from agentflow.integrations.jira.description_parser import parse_ticket_description
from agentflow.domain.jira_ticket import JiraTicket

def map_jira_issue_to_ticket(data: dict[str,Any])-> JiraTicket:

    fields = data["fields"]

    description_text = extract_adf_text(
        fields.get("description")
    )

    description, acceptance_criteria = (
            parse_ticket_description(description_text)
    )

    return JiraTicket(
        key=data["key"],
        title=fields["summary"],
        description=description,
        priority=extract_field_name(
            fields,
            "priority",
        ),

        acceptance_criteria = acceptance_criteria ,
        issue_type=extract_field_name(
            fields,
            "issuetype",
        ),
        status=extract_field_name(
            fields,
            "status",
        ),
        labels=fields.get("labels", []),
    )



def extract_field_name(fields: dict[str,Any], field_name:str)->str :
    field_data = fields.get(field_name)

    if not isinstance(field_data,dict):
        raise ValueError( f"Jira field '{field_name}' is missing or invalid."
        )

    name = field_data.get("name")

    if not isinstance(name, str) or not name.strip():
        raise ValueError(
            f"Jira field '{field_name}.name' is missing or invalid."
        )

    return name

def extract_adf_text(data: dict[str,Any])->str:

    if data is None:
        return ""

    if data.get("type") == "text":
        text = data.get("text","")
        return text if isinstance(text,str) else ""

    parts : list[str] = []

    for child in data.get("content", []):
        child_text = extract_adf_text(child)

        if child_text:
            parts.append(child_text)

    return "\n".join(parts)