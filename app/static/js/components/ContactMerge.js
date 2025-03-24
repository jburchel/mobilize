import React, { useState } from 'react';
import {
    Box,
    Button,
    Card,
    CardContent,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    FormControl,
    FormControlLabel,
    Grid,
    Radio,
    RadioGroup,
    Typography,
    Alert,
    CircularProgress
} from '@mui/material';
import { Merge as MergeIcon } from '@mui/icons-material';

const ContactMerge = ({ sourceContact, targetContact, onClose, onMergeComplete }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [mergePreview, setMergePreview] = useState(null);
    const [fieldSelections, setFieldSelections] = useState({});

    React.useEffect(() => {
        loadMergePreview();
    }, [sourceContact, targetContact]);

    const loadMergePreview = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/v1/contacts/merge/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    source_id: sourceContact.resource_name,
                    target_id: targetContact.id
                })
            });

            const data = await response.json();
            if (data.success) {
                setMergePreview(data.merge_preview);
                // Initialize selections with target values
                const initialSelections = {};
                Object.keys(data.merge_preview.fields).forEach(field => {
                    initialSelections[field] = 'target';
                });
                setFieldSelections(initialSelections);
            } else {
                setError(data.error || 'Failed to load merge preview');
            }
        } catch (err) {
            setError('Failed to load merge preview');
        } finally {
            setLoading(false);
        }
    };

    const handleFieldSelection = (field, value) => {
        setFieldSelections(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handleMerge = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('/api/v1/contacts/merge', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    source_id: sourceContact.resource_name,
                    target_id: targetContact.id,
                    field_selections: fieldSelections
                })
            });

            const data = await response.json();
            if (data.success) {
                onMergeComplete(data.merged_contact);
                onClose();
            } else {
                setError(data.error || 'Failed to merge contacts');
            }
        } catch (err) {
            setError('Failed to merge contacts');
        } finally {
            setLoading(false);
        }
    };

    const renderFieldComparison = (field, data) => {
        const fieldLabel = field.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');

        return (
            <Grid item xs={12} key={field}>
                <Card variant="outlined" sx={{ mb: 2 }}>
                    <CardContent>
                        <Typography variant="subtitle1" gutterBottom>
                            {fieldLabel}
                        </Typography>
                        <FormControl component="fieldset">
                            <RadioGroup
                                value={fieldSelections[field] || 'target'}
                                onChange={(e) => handleFieldSelection(field, e.target.value)}
                            >
                                <FormControlLabel
                                    value="target"
                                    control={<Radio />}
                                    label={
                                        <Box>
                                            <Typography variant="body2">CRM Value:</Typography>
                                            <Typography>{data.target || '(empty)'}</Typography>
                                        </Box>
                                    }
                                />
                                <FormControlLabel
                                    value="source"
                                    control={<Radio />}
                                    label={
                                        <Box>
                                            <Typography variant="body2">Google Value:</Typography>
                                            <Typography>{data.source || '(empty)'}</Typography>
                                        </Box>
                                    }
                                />
                            </RadioGroup>
                        </FormControl>
                    </CardContent>
                </Card>
            </Grid>
        );
    };

    return (
        <Dialog open maxWidth="md" fullWidth>
            <DialogTitle>
                Resolve Contact Merge
            </DialogTitle>
            <DialogContent>
                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                {loading ? (
                    <Box display="flex" justifyContent="center" p={4}>
                        <CircularProgress />
                    </Box>
                ) : mergePreview && (
                    <Grid container spacing={2}>
                        <Grid item xs={12}>
                            <Typography variant="body2" color="textSecondary" gutterBottom>
                                Select which value to keep for each field where there are differences
                            </Typography>
                        </Grid>
                        {Object.entries(mergePreview.fields)
                            .filter(([_, data]) => data.different)
                            .map(([field, data]) => renderFieldComparison(field, data))
                        }
                    </Grid>
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose} disabled={loading}>
                    Cancel
                </Button>
                <Button
                    onClick={handleMerge}
                    variant="contained"
                    color="primary"
                    startIcon={<MergeIcon />}
                    disabled={loading || !mergePreview}
                >
                    Merge Contacts
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default ContactMerge; 