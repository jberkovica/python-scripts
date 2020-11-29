from jira import JIRA
import json
import re

import config
from slack_notify import post_message_to_slack_channels


tables_exceptions = {
    'table_name': '',
    'table_id': '',
    'table_location': '',
    'studio_location': '',
    'stream_names': '',
    'operating_days_hours': 'TABLE-937, TABLE-940, TABLE-1231, TABLE-398',
    'slack': ''
}

valid_timezones = 'RIX, CET, UK, PST, GET, EDT'


def create_jira_conn():
    jira_username = config.jira_user['username']
    jira_password = config.jira_user['password']
    jira_url = config.jira_user['url']
    return JIRA(jira_url, basic_auth=(jira_username, jira_password))


def get_operating_tables_jiras(jira):

    operating_tables_jira_query = 'project=\"TABLE\" and status = Operational order by \"Table ID\"'
    operating_tables_jiras = jira.search_issues(operating_tables_jira_query, maxResults=1000)

    """
    Required jira fields:
        Table Name : customfield_10649
        Table ID : customfield_10873
        Table Location : customfield_12311
        Studio Location : customfield_12772
        Stream Names : customfield_12324
        Operating Days & Hours : customfield_16541
        Slack : customfield_14643
    """

    operating_tables_fields = {}

    for table_jira in operating_tables_jiras:
        issue = jira.issue(table_jira)
        issue_fields = {
            'table_name': str(issue.fields.customfield_10649.encode('utf-8')),
            'table_id': str(int(issue.fields.customfield_10873)),
            'table_location': str(issue.fields.customfield_12311),
            'studio_location': str(issue.fields.customfield_12772),
            'stream_names': str(issue.fields.customfield_12324),
            'operating_days_hours': str(issue.fields.customfield_16541),
            'slack': str(issue.fields.customfield_14643)
        }

        operating_tables_fields[issue.key] = issue_fields

    return operating_tables_fields


def check_not_empty(field, tables_jiras):
    empty_fields = {}

    for table, fields in tables_jiras.items():
        if fields[field] == 'None':
            reason = f'{table} has empty field: {field}'
            print(reason)
            post_message_to_slack_channels(table, reason)
            empty_fields[table] = fields

    return empty_fields


def check_table_name(tables_jiras):
    field = 'table_name'
    empty_table_name = check_not_empty(field, tables_jiras)
    return empty_table_name


def check_table_id(tables_jiras):
    field = 'table_id'
    empty_table_id = check_not_empty(field, tables_jiras)
    return empty_table_id


def check_table_location(tables_jiras):
    field = 'table_location'
    empty_table_location = check_not_empty(field, tables_jiras)
    return empty_table_location


def check_studio_location(tables_jiras):
    field = 'studio_location'
    empty_studio_location = check_not_empty(field, tables_jiras)
    return empty_studio_location


def check_stream_names(tables_jiras):
    field = 'stream_names'
    empty_stream_names = check_not_empty(field, tables_jiras)
    return empty_stream_names


def check_operating_days_hours(tables_jiras):

    field_name = 'operating_days_hours'
    jiras_with_wrong_operating_days_hours = {}
    exceptions = tables_exceptions['operating_days_hours']

    for table, fields in tables_jiras.items():

        if table in exceptions:
            continue

        operating_days_hours = fields[field_name].splitlines()

        if len(operating_days_hours) < 2:
            reason = f'{table} has NOT enough data in operating_days_hours field'
            print(reason)
            post_message_to_slack_channels(table, reason)
            jiras_with_wrong_operating_days_hours[table] = fields
            continue

        timezone = operating_days_hours[0].strip()
        working_hours = operating_days_hours[1]

        if timezone not in valid_timezones:
            reason = f'{table} has invalid timezone: {timezone}'
            print(reason)
            post_message_to_slack_channels(table, reason)
            jiras_with_wrong_operating_days_hours[table] = fields
            continue

        """
        expected working hours style:
            24h
            00.00-24.00
            00-24
            Mon,Tue,Wed,Thu,Fri:16.50-00.55
        """
        regex1 = re.compile(r'[0-2][0-4]h')
        regex2 = re.compile(r'[0-2][0-9]\.[0-5][0-9]-[0-2][0-9]\.[0-5][0-9]')
        regex3 = re.compile(r'[0-2][0-4]-[0-2][0-4]')
        regex_list = [regex1, regex2, regex3]

        regex_matches = False
        for regex in regex_list:
            if regex.match(working_hours):
                regex_matches = True
                break

        if not regex_matches:
            reason = f'{table} has invalid working_hours: {working_hours}'
            print(reason)
            post_message_to_slack_channels(channel=config.slack_channel, url=jira_url, jira=table, reason=reason)
            jiras_with_wrong_operating_days_hours[table] = fields
            continue

    return jiras_with_wrong_operating_days_hours


def check_slack(tables_jiras):
    field = 'slack'
    empty_slack = check_not_empty(field, tables_jiras)
    return empty_slack


def get_table_jiras():
    jira = create_jira_conn()
    table_jiras = get_operating_tables_jiras(jira)
    with open('data/operating_tables.json', 'w', encoding='utf-8') as f:
        json.dump(table_jiras, f, ensure_ascii=False, indent=4)
    return table_jiras


def get_table_jiras_from_json():
    with open('data/operating_tables.json') as f:
        table_jiras = json.load(f)
    return table_jiras


def analyze_table_jiras(table_jiras):
    """Analyze table jiras fields, creates JSON output and reports problem to Slack"""

    tables_with_problems = {
        'table_name_problems': check_table_name(table_jiras),
        'table_id_problems': check_table_id(table_jiras),
        'table_location_problems': check_table_location(table_jiras),
        'studio_location_problems': check_studio_location(table_jiras),
        'stream_names_problems': check_stream_names(table_jiras),
        'operating_days_hours_problems': check_operating_days_hours(table_jiras),
        'slack_problems': check_slack(table_jiras)
    }
    with open('data/tables_with_problems.json', 'w', encoding='utf-8') as f:
        json.dump(tables_with_problems, f, ensure_ascii=False, indent=4)


def cleanup():
    return


if __name__ == "__main__":

    # TODO: add check if file exist and delete file at the end?

    # use 'get_table_jiras' or 'get_table_jiras_from_json':
    operating_tables = get_table_jiras_from_json()
    analyze_table_jiras(operating_tables)



