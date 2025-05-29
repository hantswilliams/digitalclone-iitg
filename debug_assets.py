#!/usr/bin/env python3
"""
Debug script to check asset data for video generation troubleshooting
"""
import sys
import os
sys.path.append('/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend')

from app import create_app
from app.models import Asset, Job
from app.models.asset import AssetType, AssetStatus

def debug_assets():
    app = create_app()
    
    with app.app_context():
        print("=== RECENT JOBS ===")
        recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()
        for job in recent_jobs:
            print(f"Job {job.id}: {job.job_type.value}, User: {job.user_id}, Status: {job.status.value}")
            if job.parameters:
                print(f"  Parameters: {job.parameters}")
            print()
        
        print("=== ALL ASSETS ===")
        assets = Asset.query.order_by(Asset.created_at.desc()).limit(20).all()
        for asset in assets:
            print(f"Asset {asset.id}: {asset.asset_type}, User: {asset.user_id}, Status: {asset.status}")
            print(f"  Filename: {asset.filename}")
            print(f"  Created: {asset.created_at}")
            print()
        
        print("=== PORTRAIT ASSETS ===")
        portraits = Asset.query.filter_by(asset_type='portrait').all()
        for asset in portraits:
            print(f"Portrait {asset.id}: User {asset.user_id}, Status: {asset.status}, File: {asset.filename}")
        
        print("=== VOICE ASSETS ===")
        voice_assets = Asset.query.filter(Asset.asset_type.like('%voice%')).all()
        for asset in voice_assets:
            print(f"Voice {asset.id}: Type {asset.asset_type}, User {asset.user_id}, Status: {asset.status}, File: {asset.filename}")
        
        print("=== TESTING ENUM-BASED QUERIES ===")
        # Test the specific lookup that was failing
        job_113_portrait = Asset.query.filter_by(
            id=57,
            user_id=53,
            asset_type=AssetType.PORTRAIT
        ).first()
        
        job_113_voice = Asset.query.filter_by(
            id=61,
            user_id=53,
            asset_type=AssetType.VOICE_SAMPLE
        ).first()
        
        print(f"Portrait asset 57 for user 53: {job_113_portrait}")
        if job_113_portrait:
            print(f"  Status: {job_113_portrait.status} (Ready? {job_113_portrait.status == AssetStatus.READY})")
        
        print(f"Voice asset 61 for user 53: {job_113_voice}")
        if job_113_voice:
            print(f"  Status: {job_113_voice.status} (Ready? {job_113_voice.status == AssetStatus.READY})")
        print()

if __name__ == '__main__':
    debug_assets()
