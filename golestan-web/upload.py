import sys
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError

def backup(LOCALFILE, BACKUPPATH, dbx):
    with open(LOCALFILE, 'rb') as f:
        try:
            dbx.files_upload(f.read(), BACKUPPATH, mode=WriteMode('add', None), autorename=True, mute=True)
            url = str(dbx.sharing_create_shared_link_with_settings(BACKUPPATH).url).split('?')[0] + '?raw=1'
            return url
        except ApiError as err:

            if (err.error.is_path() and
                    err.error.get_path().error.is_insufficient_space()):
                print("ERROR: Cannot back up; insufficient space.")
            elif err.user_message_text:
                print(err.user_message_text)
            else:
                print(err)

            return ''


def upload_file(LOCALFILE, BACKUPPATH,
                TOKEN='sl.BipyM9lt2P-ofAABGwpubRNzSJfutxGmh8RcGqhnYlbArb5lkhYOlfZo8tY9ggisQCMj0Pf3-R36lrNgYucAf9OhhLBFkpxwf1hbbOONrkistzn51yqQte-VCd_t2-mTm-7lU0MFanNqBli2YJLZ0dU'):
    if (len(TOKEN) == 0):
        print(
            "ERROR: Looks like you didn't add your access token. Open up backup-and-restore-example.py in a text editor and paste in your token in line 14.")
        return ''

    dbx = dropbox.Dropbox(TOKEN)

    try:
        dbx.users_get_current_account()
    except AuthError as err:
        print(
            "ERROR: Invalid access token; try re-generating an access token from the app console on the web.")
        return ''

    return backup(LOCALFILE, BACKUPPATH, dbx)


dbname = 'db.sqlite3'
print(upload_file(dbname, f'/{dbname}'))
