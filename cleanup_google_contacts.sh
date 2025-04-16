#!/bin/bash

# Script to clean up Google-synced contacts
# This will delete any contacts that were synced from Google but not properly
# associated with people or churches (type = 'contact')

echo "Checking for Google contacts in mobilize_crm.db..."
GOOGLE_CONTACTS=$(sqlite3 instance/mobilize_crm.db "SELECT COUNT(*) FROM contacts WHERE type = 'contact' AND google_contact_id IS NOT NULL;")

echo "Found $GOOGLE_CONTACTS Google-synced contacts that aren't properly associated with people or churches."

read -p "Do you want to delete these contacts? (y/n): " CONFIRM

if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
    echo "Deleting Google contacts..."
    sqlite3 instance/mobilize_crm.db "DELETE FROM contacts WHERE type = 'contact' AND google_contact_id IS NOT NULL;"
    REMAINING=$(sqlite3 instance/mobilize_crm.db "SELECT COUNT(*) FROM contacts;")
    echo "Done! $GOOGLE_CONTACTS contacts deleted. $REMAINING contacts remain in the database."
else
    echo "Operation cancelled. No contacts were deleted."
fi

echo "NOTE: To prevent this issue in the future, use the 'Import' feature instead of 'Sync'"
echo "      to select specific contacts to import from Google." 