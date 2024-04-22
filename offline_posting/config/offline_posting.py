from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
	        {
            "label": _("Offline Posting"),
             "items": [
                {
                    "type": "doctype",
                    "name": "Offline Sync",
                    "label": _("Offline Sync"),
                    "description": _("Sync pending data uploads and downloads")
               
                }
            ],
        }
	]

