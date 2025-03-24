import React, { useState, useEffect } from 'react';
import {
    Box,
    Button,
    Checkbox,
    CircularProgress,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Paper,
    Typography,
    Alert,
    IconButton,
} from '@mui/material';
import { 
    Sync as SyncIcon, 
    Person as PersonIcon,
    Merge as MergeIcon
} from '@mui/icons-material';
import ContactMerge from './ContactMerge';

const ContactSync = () => {
    const [contacts, setContacts] = useState([]);
    const [selectedContacts, setSelectedContacts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [syncInProgress, setSyncInProgress] = useState(false);
    const [syncStats, setSyncStats] = useState(null);
    const [mergeDialogOpen, setMergeDialogOpen] = useState(false);
    const [currentMergeContact, setCurrentMergeContact] = useState(null);

    useEffect(() => {
        loadGoogleContacts();
    }, []);

    const loadGoogleContacts = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/v1/contacts/google/preview');
            const data = await response.json();
            
            if (data.success) {
                setContacts(data.contacts);
            } else {
                setError(data.error || 'Failed to load contacts');
            }
        } catch (err) {
            setError('Failed to load Google contacts');
        } finally {
            setLoading(false);
        }
    };

    const handleToggleContact = (resourceName) => {
        setSelectedContacts(prev => {
            if (prev.includes(resourceName)) {
                return prev.filter(id => id !== resourceName);
            }
            return [...prev, resourceName];
        });
    };

    const handleSelectAll = () => {
        if (selectedContacts.length === contacts.length) {
            setSelectedContacts([]);
        } else {
            setSelectedContacts(contacts.map(c => c.resource_name));
        }
    };

    const handleSync = async () => {
        if (!selectedContacts.length) return;
        
        setSyncInProgress(true);
        setError(null);
        try {
            const response = await fetch('/api/v1/contacts/google/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    contact_ids: selectedContacts,
                    direction: 'from_google'
                })
            });
            
            const data = await response.json();
            if (data.success) {
                setSyncStats(data.stats);
            } else {
                setError(data.error || 'Sync failed');
            }
        } catch (err) {
            setError('Failed to sync contacts');
        } finally {
            setSyncInProgress(false);
        }
    };

    const handleMergeClick = (contact) => {
        setCurrentMergeContact(contact);
        setMergeDialogOpen(true);
    };

    const handleMergeComplete = (mergedContact) => {
        // Update the contacts list after merge
        setContacts(prevContacts => 
            prevContacts.map(c => 
                c.resource_name === currentMergeContact.resource_name
                    ? { ...c, has_duplicate: false }
                    : c
            )
        );
        setMergeDialogOpen(false);
        setCurrentMergeContact(null);
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" p={4}>
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Paper sx={{ p: 3, maxWidth: 800, margin: 'auto' }}>
            <Box mb={3}>
                <Typography variant="h5" gutterBottom>
                    Google Contacts Sync
                </Typography>
                <Typography color="textSecondary">
                    Select contacts to import from Google
                </Typography>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            {syncStats && (
                <Alert severity="success" sx={{ mb: 3 }}>
                    Sync completed: {syncStats.created} created, {syncStats.updated} updated
                </Alert>
            )}

            <Box mb={2}>
                <Button
                    variant="outlined"
                    onClick={handleSelectAll}
                    disabled={loading || syncInProgress}
                >
                    {selectedContacts.length === contacts.length ? 'Deselect All' : 'Select All'}
                </Button>
                <Button
                    variant="contained"
                    color="primary"
                    startIcon={<SyncIcon />}
                    onClick={handleSync}
                    disabled={!selectedContacts.length || syncInProgress}
                    sx={{ ml: 2 }}
                >
                    Sync Selected
                </Button>
            </Box>

            <List>
                {contacts.map((contact) => (
                    <ListItem
                        key={contact.resource_name}
                        button
                        onClick={() => handleToggleContact(contact.resource_name)}
                        disabled={syncInProgress}
                        secondaryAction={
                            contact.has_duplicate && (
                                <IconButton
                                    edge="end"
                                    aria-label="merge"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleMergeClick(contact);
                                    }}
                                >
                                    <MergeIcon color="warning" />
                                </IconButton>
                            )
                        }
                    >
                        <ListItemIcon>
                            <Checkbox
                                checked={selectedContacts.includes(contact.resource_name)}
                                disableRipple
                            />
                        </ListItemIcon>
                        <ListItemIcon>
                            <PersonIcon color={contact.has_duplicate ? "warning" : "inherit"} />
                        </ListItemIcon>
                        <ListItemText
                            primary={`${contact.google_data.first_name} ${contact.google_data.last_name}`}
                            secondary={contact.google_data.email || 'No email'}
                        />
                        {contact.has_duplicate && (
                            <Typography variant="caption" color="warning.main" sx={{ mr: 2 }}>
                                Potential duplicate
                            </Typography>
                        )}
                    </ListItem>
                ))}
            </List>

            {mergeDialogOpen && currentMergeContact && (
                <ContactMerge
                    sourceContact={currentMergeContact}
                    targetContact={currentMergeContact.duplicate_info}
                    onClose={() => {
                        setMergeDialogOpen(false);
                        setCurrentMergeContact(null);
                    }}
                    onMergeComplete={handleMergeComplete}
                />
            )}
        </Paper>
    );
};

export default ContactSync; 