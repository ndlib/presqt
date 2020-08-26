from presqt.utilities import write_file, read_file


def update_process_info_download(process_info_path, total_files, action):
    """
    Update the process_info.json file with the number of total files involved in the action

    Parameters
    ----------
    process_info_path: str
        Path to the process_info.json file to update
    total_files: int
        Total number of resources involved in the action
    action: str
        The action to update in the process_info.json object
    """
    process_info_data = read_file(process_info_path, True)
    process_info_data[action]['download_total_files'] = total_files
    write_file(process_info_path, process_info_data, True)
    return


def update_process_info_upload(process_info_path, total_files, action):
    """
    Update the process_info.json file with the number of total files involved in the action

    Parameters
    ----------
    process_info_path: str
        Path to the process_info.json file to update
    total_files: int
        Total number of resources involved in the action
    action: str
        The action to update in the process_info.json object
    """
    process_info_data = read_file(process_info_path, True)
    process_info_data[action]['upload_total_files'] = total_files
    write_file(process_info_path, process_info_data, True)
    return

def update_process_info(process_info_path, total_files, action):
    """
    Update the process_info.json file with the number of total files involved in the action

    Parameters
    ----------
    process_info_path: str
        Path to the process_info.json file to update
    total_files: int
        Total number of resources involved in the action
    action: str
        The action to update in the process_info.json object
    """
    process_info_data = read_file(process_info_path, True)
    process_info_data[action]['total_files'] = total_files
    write_file(process_info_path, process_info_data, True)
    return


def increment_process_info_download(process_info_path, action):
    """
    Increment the download_files_finished attribute in the process_info.json file

    Parameters
    ----------
    process_info_path: str
        Path to the process_info.json file to update
    action: str
        The action to update in the process_info.json object
    """
    process_info_data = read_file(process_info_path, True)
    process_info_data[action]['download_files_finished'] = process_info_data[action]['download_files_finished'] + 1
    write_file(process_info_path, process_info_data, True)
    return


def increment_process_info_upload(process_info_path, action):
    """
    Increment the upload_files_finished attribute in the process_info.json file

    Parameters
    ----------
    process_info_path: str
        Path to the process_info.json file to update
    action: str
        The action to update in the process_info.json object
    """
    process_info_data = read_file(process_info_path, True)
    process_info_data[action]['upload_files_finished'] = process_info_data[action]['upload_files_finished'] + 1
    write_file(process_info_path, process_info_data, True)
    return

def increment_process_info(process_info_path, action):
    """
    Increment the download_files_finished attribute in the process_info.json file

    Parameters
    ----------
    process_info_path: str
        Path to the process_info.json file to update
    action: str
        The action to update in the process_info.json object
    """
    process_info_data = read_file(process_info_path, True)
    process_info_data[action]['files_finished'] = process_info_data[action]['files_finished'] + 1
    write_file(process_info_path, process_info_data, True)
    return


def update_process_info_message(process_info_path, action, message):
    """
    Update the process_info.json file with the number of total files involved in the action

    Parameters
    ----------
    process_info_path: str
        Path to the process_info.json file to update
    action: str
        The action to update in the process_info.json object
    message: str
        The message to add to the process_info file
    """
    process_info_data = read_file(process_info_path, True)
    process_info_data[action]['message'] = message
    write_file(process_info_path, process_info_data, True)
    return
