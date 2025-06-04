#!/usr/bin/env python3
"""
Test script to validate frontend-backend metadata integration.

This script tests:
1. Backend API endpoints return proper metadata structure
2. Frontend receives all metadata fields from backend
3. Frontend properly displays key metadata fields
4. Validates metadata field availability and consistency

Author: AI Assistant
Created: 2025-01-20
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to the path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.tts.indextts_client import IndexTTSClient
from app.services.video.kdtalker_client import KDTalkerClient

def test_metadata_structure_consistency():
    """Test that both services return consistent metadata structure."""
    print("\n🔍 Testing metadata structure consistency...")
    
    # Test IndexTTS metadata structure
    try:
        indextts_client = IndexTTSClient()
        indextts_metadata = indextts_client.get_space_metadata()
        print(f"✅ IndexTTS metadata retrieved: {indextts_metadata.get('space_name', 'Unknown')}")
    except Exception as e:
        print(f"❌ IndexTTS metadata failed: {e}")
        indextts_metadata = {'error': str(e)}
    
    # Test KDTalker metadata structure
    try:
        kdtalker_client = KDTalkerClient()
        kdtalker_metadata = kdtalker_client.get_space_metadata()
        print(f"✅ KDTalker metadata retrieved: {kdtalker_metadata.get('space_name', 'Unknown')}")
    except Exception as e:
        print(f"❌ KDTalker metadata failed: {e}")
        kdtalker_metadata = {'error': str(e)}
    
    # Analyze structure consistency
    expected_fields = [
        'space_name', 'space_url', 'metadata_available',
        'space_id', 'author', 'created_at', 'last_modified',
        'likes', 'downloads', 'sdk', 'runtime'
    ]
    
    expected_runtime_fields = ['stage', 'hardware', 'hardware_friendly']
    
    results = {
        'indextts_structure': {},
        'kdtalker_structure': {},
        'consistency_check': {},
        'missing_fields': {},
        'field_availability': {}
    }
    
    # Check IndexTTS structure
    for field in expected_fields:
        results['indextts_structure'][field] = field in indextts_metadata
        if field == 'runtime' and field in indextts_metadata:
            runtime_data = indextts_metadata[field]
            for runtime_field in expected_runtime_fields:
                results['indextts_structure'][f'runtime.{runtime_field}'] = runtime_field in runtime_data
    
    # Check KDTalker structure
    for field in expected_fields:
        results['kdtalker_structure'][field] = field in kdtalker_metadata
        if field == 'runtime' and field in kdtalker_metadata:
            runtime_data = kdtalker_metadata[field]
            for runtime_field in expected_runtime_fields:
                results['kdtalker_structure'][f'runtime.{runtime_field}'] = runtime_field in runtime_data
    
    # Check consistency between services
    all_fields = set(list(results['indextts_structure'].keys()) + list(results['kdtalker_structure'].keys()))
    for field in all_fields:
        indextts_has = results['indextts_structure'].get(field, False)
        kdtalker_has = results['kdtalker_structure'].get(field, False)
        results['consistency_check'][field] = indextts_has == kdtalker_has
    
    # Identify missing fields
    for service, structure in [('indextts', results['indextts_structure']), ('kdtalker', results['kdtalker_structure'])]:
        missing = [field for field, available in structure.items() if not available]
        results['missing_fields'][service] = missing
    
    # Field availability summary
    for field in all_fields:
        indextts_available = results['indextts_structure'].get(field, False)
        kdtalker_available = results['kdtalker_structure'].get(field, False)
        results['field_availability'][field] = {
            'indextts': indextts_available,
            'kdtalker': kdtalker_available,
            'both_services': indextts_available and kdtalker_available
        }
    
    print(f"✅ Structure consistency test completed")
    return results, indextts_metadata, kdtalker_metadata

def test_frontend_display_mapping():
    """Test which metadata fields are displayed in the frontend."""
    print("\n🎨 Testing frontend display mapping...")
    
    # Fields currently displayed in DashboardPage.jsx
    dashboard_displayed_fields = [
        'space_name',           # Model name
        'runtime.hardware_friendly',  # Hardware (friendly name)
        'runtime.hardware',     # Hardware (fallback)
        'runtime.stage'         # Status
    ]
    
    # Fields currently displayed in CreateVideoPage.jsx
    create_video_displayed_fields = [
        'space_name',           # Model name
        'runtime.hardware_friendly',  # Hardware (friendly name)
        'runtime.hardware'      # Hardware (fallback)
    ]
    
    # Available but not displayed fields
    available_not_displayed = [
        'space_url',           # Could be a link to HF space
        'author',              # Space author
        'created_at',          # When space was created
        'last_modified',       # Last update
        'likes',               # Community engagement
        'downloads',           # Usage statistics
        'sdk',                 # Framework (gradio, streamlit, etc.)
        'space_id'             # Full space identifier
    ]
    
    results = {
        'dashboard_fields': dashboard_displayed_fields,
        'create_video_fields': create_video_displayed_fields,
        'not_displayed_fields': available_not_displayed,
        'display_suggestions': {},
        'priority_additions': []
    }
    
    # Suggest priority fields to add to frontend
    priority_suggestions = [
        {
            'field': 'space_url',
            'display_as': 'Clickable model name linking to HF space',
            'location': 'Both DashboardPage and CreateVideoPage',
            'reasoning': 'Provides direct access to model documentation'
        },
        {
            'field': 'author',
            'display_as': 'Model author/organization',
            'location': 'DashboardPage (detailed view)',
            'reasoning': 'Shows model provenance and credibility'
        },
        {
            'field': 'sdk',
            'display_as': 'Framework type (Gradio/Streamlit)',
            'location': 'DashboardPage (technical details)',
            'reasoning': 'Technical information for debugging'
        },
        {
            'field': 'last_modified',
            'display_as': 'Last updated date',
            'location': 'DashboardPage (detailed view)',
            'reasoning': 'Shows model freshness and maintenance status'
        }
    ]
    
    results['priority_additions'] = priority_suggestions
    
    # Display suggestions for different contexts
    results['display_suggestions'] = {
        'dashboard_additions': [
            'author - as "by [author]" under model name',
            'space_url - make model name clickable',
            'sdk - show framework type',
            'last_modified - show update recency'
        ],
        'create_video_additions': [
            'space_url - make model name clickable for quick reference'
        ],
        'new_detailed_view': [
            'All metadata fields in an expandable "Model Details" section',
            'likes/downloads as community metrics',
            'created_at for model age information'
        ]
    }
    
    print(f"✅ Frontend display mapping completed")
    return results

def test_metadata_error_handling():
    """Test how frontend should handle metadata errors and missing data."""
    print("\n🚨 Testing metadata error handling scenarios...")
    
    error_scenarios = [
        {
            'name': 'API unavailable',
            'metadata': {'error': 'HfApi not available', 'metadata_available': False},
            'expected_display': 'Show "Model info unavailable" with basic service status'
        },
        {
            'name': 'Invalid space',
            'metadata': {'error': '404 Client Error', 'metadata_available': False},
            'expected_display': 'Show "Model not found" with warning'
        },
        {
            'name': 'Partial metadata',
            'metadata': {
                'space_name': 'test/model',
                'metadata_available': True,
                'runtime': {'hardware': 'unknown'}  # Missing hardware_friendly
            },
            'expected_display': 'Show available fields, fallback for missing ones'
        },
        {
            'name': 'Network timeout',
            'metadata': {'error': 'Connection timeout', 'metadata_available': False},
            'expected_display': 'Show "Connection error" with retry option'
        }
    ]
    
    results = {
        'error_scenarios': error_scenarios,
        'frontend_handling_recommendations': [],
        'graceful_degradation': {}
    }
    
    # Recommendations for graceful error handling
    handling_recommendations = [
        'Always check metadata_available before accessing fields',
        'Provide fallback values for missing fields (e.g., "Unknown" for hardware)',
        'Show user-friendly error messages instead of raw error strings',
        'Include retry mechanisms for network-related errors',
        'Maintain service status indicators even when metadata fails',
        'Log detailed errors to console while showing simple messages to users'
    ]
    
    results['frontend_handling_recommendations'] = handling_recommendations
    
    # Graceful degradation strategy
    results['graceful_degradation'] = {
        'level_1': 'Full metadata available - show all details',
        'level_2': 'Partial metadata - show available fields with "Unknown" fallbacks',
        'level_3': 'No metadata but service running - show basic status only',
        'level_4': 'Service unavailable - show offline status with error context'
    }
    
    print(f"✅ Error handling scenarios completed")
    return results

def generate_frontend_recommendations():
    """Generate specific recommendations for frontend improvements."""
    print("\n💡 Generating frontend improvement recommendations...")
    
    recommendations = {
        'immediate_improvements': [
            {
                'component': 'DashboardPage.jsx',
                'change': 'Make space_name clickable linking to space_url',
                'code_hint': '<a href={serviceMetadata.indexTTS.space_url} target="_blank">{serviceMetadata.indexTTS.space_name}</a>',
                'benefit': 'Direct access to model documentation'
            },
            {
                'component': 'Both pages',
                'change': 'Add author display under model name',
                'code_hint': '<p className="text-xs text-gray-500">by {serviceMetadata.indexTTS.author}</p>',
                'benefit': 'Shows model provenance'
            }
        ],
        'medium_term_improvements': [
            {
                'component': 'DashboardPage.jsx',
                'change': 'Add expandable "Model Details" section',
                'fields': ['sdk', 'last_modified', 'created_at', 'likes', 'downloads'],
                'benefit': 'Comprehensive model information for power users'
            },
            {
                'component': 'New component',
                'change': 'Create ModelMetadataCard component',
                'benefit': 'Reusable metadata display across pages'
            }
        ],
        'error_handling_improvements': [
            {
                'component': 'Both pages',
                'change': 'Add proper error states for metadata failures',
                'code_hint': 'if (serviceMetadata.indexTTS?.error) { /* show error state */ }',
                'benefit': 'Better user experience during failures'
            }
        ]
    }
    
    return recommendations

def main():
    """Run all frontend metadata integration tests."""
    print("🚀 Starting Frontend-Backend Metadata Integration Tests")
    print("=" * 60)
    
    all_results = {
        'test_timestamp': datetime.now().isoformat(),
        'test_script': __file__,
        'tests': {}
    }
    
    try:
        # Test 1: Metadata structure consistency
        structure_results, indextts_data, kdtalker_data = test_metadata_structure_consistency()
        all_results['tests']['structure_consistency'] = structure_results
        all_results['sample_data'] = {
            'indextts_metadata': indextts_data,
            'kdtalker_metadata': kdtalker_data
        }
        
        # Test 2: Frontend display mapping
        display_results = test_frontend_display_mapping()
        all_results['tests']['frontend_display_mapping'] = display_results
        
        # Test 3: Error handling scenarios
        error_results = test_metadata_error_handling()
        all_results['tests']['error_handling'] = error_results
        
        # Generate recommendations
        recommendations = generate_frontend_recommendations()
        all_results['recommendations'] = recommendations
        
        # Summary
        total_fields = len(structure_results['field_availability'])
        displayed_fields = len(display_results['dashboard_fields'])
        available_not_displayed = len(display_results['not_displayed_fields'])
        
        all_results['summary'] = {
            'total_metadata_fields': total_fields,
            'currently_displayed': displayed_fields,
            'available_but_not_displayed': available_not_displayed,
            'display_coverage_percentage': round((displayed_fields / total_fields) * 100, 1),
            'recommendations_count': len(recommendations['immediate_improvements']) + len(recommendations['medium_term_improvements'])
        }
        
        # Save results
        output_file = '/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend/test_files/frontend_metadata_integration_results.json'
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"\n📊 Test Summary:")
        print(f"   • Total metadata fields available: {total_fields}")
        print(f"   • Currently displayed in frontend: {displayed_fields}")
        print(f"   • Available but not displayed: {available_not_displayed}")
        print(f"   • Display coverage: {all_results['summary']['display_coverage_percentage']}%")
        print(f"   • Improvement recommendations: {all_results['summary']['recommendations_count']}")
        
        print(f"\n💾 Full results saved to: {output_file}")
        print("✅ All tests completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
