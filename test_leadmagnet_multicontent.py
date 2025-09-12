#!/usr/bin/env python3
"""Test lead magnet multi-content functionality"""

import asyncio
import sys
sys.path.append('.')

async def test_lead_magnet():
    """Test basic lead magnet functionality"""
    try:
        from database.lead_magnet import LeadMagnet
        
        # Test getting lead magnet
        print("🧪 Testing LeadMagnet.get_lead_magnet()...")
        lm = await LeadMagnet.get_lead_magnet()
        if lm:
            print(f"✅ Lead magnet found: id={lm.id}")
            print(f"   - enabled: {lm.enabled}")
            print(f"   - content_type: {getattr(lm, 'content_type', 'NOT FOUND')}")
            print(f"   - video_file_id: {getattr(lm, 'video_file_id', 'NOT FOUND')}")
            print(f"   - photo_file_id: {getattr(lm, 'photo_file_id', 'NOT FOUND')}")
            print(f"   - document_file_id: {getattr(lm, 'document_file_id', 'NOT FOUND')}")
        else:
            print("❌ Lead magnet not found")
            return False
        
        # Test get_current_content
        print("\n🧪 Testing LeadMagnet.get_current_content()...")
        content_type, file_id = await LeadMagnet.get_current_content()
        print(f"✅ Current content: type={content_type}, file_id={file_id}")
        
        # Test is_ready
        print("\n🧪 Testing LeadMagnet.is_ready()...")
        is_ready = await LeadMagnet.is_ready()
        print(f"✅ Is ready: {is_ready}")
        
        # Test setting content
        print("\n🧪 Testing LeadMagnet.set_content()...")
        test_result = await LeadMagnet.set_content('photo', 'test_photo_id_123')
        print(f"✅ Set photo content: {test_result}")
        
        # Verify content was set
        content_type, file_id = await LeadMagnet.get_current_content()
        print(f"✅ Verified content: type={content_type}, file_id={file_id}")
        
        # Test _has_content
        print("\n🧪 Testing LeadMagnet._has_content()...")
        lm_updated = await LeadMagnet.get_lead_magnet()
        has_content = LeadMagnet._has_content(lm_updated)
        print(f"✅ Has content: {has_content}")
        
        print("\n🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Testing Lead Magnet Multi-Content Functionality")
    print("=" * 60)
    
    success = asyncio.run(test_lead_magnet())
    
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)