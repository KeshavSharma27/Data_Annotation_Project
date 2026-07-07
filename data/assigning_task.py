from label_studio_sdk import LabelStudio
import os
import sys
from api import api, url

base_url = url()
api_key = api()



client = LabelStudio(base_url = base_url, api_key = api_key)
me = client.users.whoami()


label_config= """
<View>
    <Header value="choose the Behaviour:"/>
    <Text name="text" value="$text"/>
    <Choices name="sentiment" toName="text" choice="single">
        <Choice value="Good"/>
        <Choice value="Bad"/>
    </Choices>
</View>
"""
workspaces = client.workspaces.list()

for ws in workspaces:
    print(ws.id, ws.title)

project = client.projects.create(
    title="Behaviour Classification", 
    label_config = label_config,
    workspace = 165947
)

project_id =  project.id



tasks = [
    {"text": "She greets everyone in the morning."},
    {"text": "Someone is irritating him there."},
    {"text": "They made fun of his work."},
    {"text": "They feed to animals daily at night."},
    {"text": "He shouts at an elder person"}
]


resp = client.projects.import_tasks(
    id=project_id,
    request=tasks,
    return_task_ids=True,
)

if not api_key or not base_url:
    print("Error: set LABEL_STUDIO_API_KEY and LABEL_STUDIO_URL ")
    sys.exit(1)

user_email = "shrutidwivedi894@gmail.com"
assignment_type = (
    sys.argv[3].strip().upper() if len(sys.argv)>3 else "AN"
)

print(f"Project: {project.title} (id = {project.id})")

users = list(client.users.list())
user = next(
    (u for u in users if (u.email or "").lower() == user_email.lower()), None)
if not user:
    print(f"Error: user with email {user_email} not found")
    sys.exit(1)

print(f"User: {user.email} (id={user.id})")

filters = {
    "conjunction": "and",
    "items": [
        {
            "filter": "filter:tasks:inner_id",
            "operator": "greater",
            "value": 0,
            "child_filter": None,
            "type": "Number",
        },
        {
            "filter": "filter:tasks:inner_id",
            "operator": "less",
            "value": 5,
            "child_filter": None,
            "type": "Number",
        },
    ],
}
selected_items = {"all": True}


resp = client.projects.assignments.bulk_assign(
    id = project_id,
    type= assignment_type,
    users = [user.id],
    selected_items = selected_items,
    filters= filters,
)

print(f"Bulk assignment done: {resp}")   



    