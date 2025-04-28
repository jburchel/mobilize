#!/usr/bin/env python3
"""
Script to seed all Person records into the main people pipeline stages.
Usage: python scripts/pipeline_management/add_people_to_pipeline.py
"""
import os
import sys
from datetime import datetime

# Set up environment (adjust if needed)
os.environ.setdefault('FLASK_APP', 'run_dev.py')
os.environ.setdefault('FLASK_ENV', 'development')
# Ensure project root is in Python path
sys.path.insert(0, os.getcwd())

from flask import Flask
from app import create_app
from app.extensions import db
from app.models import Person, Pipeline, PipelineStage, PipelineContact

app = create_app()

with app.app_context():
    # Find the main people pipeline
    people_pipeline = Pipeline.query.filter(
        Pipeline.is_main_pipeline == True,
        Pipeline.pipeline_type.in_(['person', 'people'])
    ).first()

    if not people_pipeline:
        print("No main people pipeline found.")
        exit(1)

    # Get the first stage for this pipeline
    first_stage = PipelineStage.query.filter_by(
        pipeline_id=people_pipeline.id
    ).order_by(PipelineStage.order.asc()).first()

    if not first_stage:
        print(f"No stages found for pipeline {people_pipeline.id}. Please create stages first.")
        exit(1)

    total = 0
    for person in Person.query.all():
        exists = PipelineContact.query.filter_by(
            contact_id=person.id,
            pipeline_id=people_pipeline.id
        ).first()
        if exists:
            continue
        # Create pipeline contact for this person
        pc = PipelineContact(
            contact_id=person.id,
            pipeline_id=people_pipeline.id,
            current_stage_id=first_stage.id
        )
        # Set timestamps
        pc.created_at = datetime.utcnow()
        pc.updated_at = datetime.utcnow()
        db.session.add(pc)
        total += 1

    db.session.commit()
    print(f"Added {total} people to pipeline {people_pipeline.id}.") 