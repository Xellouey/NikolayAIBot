#!/usr/bin/env python3
"""Test lead magnet with fresh Python process"""

def test_orm():
    """Test with ORM after fresh start"""
    import asyncio
    import sys
    sys.path.append('.')
    
    async def test():
        try:
            from database.lead_magnet import LeadMagnet
            
            print("🧪 Testing with fresh ORM...")
            
            # Test get_lead_magnet
            lm = await LeadMagnet.get_lead_magnet()
            if lm:
                print(f"✅ Lead magnet: id={lm.id}, enabled={lm.enabled}")
                print(f"   content_type: {lm.content_type}")
                print(f"   video_file_id: {lm.video_file_id}")
                print(f"   photo_file_id: {lm.photo_file_id}")
                print(f"   document_file_id: {lm.document_file_id}")
            else:
                print("❌ Failed to get lead magnet")
                return False
            
            # Test get_current_content
            content_type, file_id = await LeadMagnet.get_current_content()
            print(f"✅ Current content: {content_type}, {file_id}")
            
            # Test set_content for video
            result = await LeadMagnet.set_content('video', 'test_video_456')
            print(f"✅ Set video: {result}")
            
            # Verify
            content_type, file_id = await LeadMagnet.get_current_content()
            print(f"✅ After video set: {content_type}, {file_id}")
            
            # Test set_content for photo
            result = await LeadMagnet.set_content('photo', 'test_photo_789')
            print(f"✅ Set photo: {result}")
            
            # Verify
            content_type, file_id = await LeadMagnet.get_current_content()
            print(f"✅ After photo set: {content_type}, {file_id}")
            
            print("\n🎉 All ORM tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ ORM test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return asyncio.run(test())

if __name__ == "__main__":
    success = test_orm()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")