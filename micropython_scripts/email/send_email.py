import umail
from secrets import secrets

smtp = umail.SMTP('smtp.gmail.com', 587,
                  username=secrets['gmail_username'],
                  password=secrets['gmail_password'])
smtp.to('dblanding@gmail.com')
smtp.send("This is an example.")
smtp.quit()
