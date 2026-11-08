import asyncio
from unittest.mock import MagicMock
from textual.pilot import Pilot

from alibi.ui.app import TheAlibiApp
from alibi.llm.client import OllamaClient

def test_ui_full_screens_flow():
    """Test full TUI screens, navigation, modals, and keybindings using asyncio.run."""
    async def _async_test():
        mock_client = MagicMock()
        mock_client.get_embeddings.return_value = [0.05] * 768
        mock_client.get_installed_models.return_value = ["llama3.1:latest", "nomic-embed-text:latest"]
        mock_client.verify_models.return_value = (True, "OK")

        app = TheAlibiApp(client=mock_client, saves_path="saves/test_ui_progress.json")
        
        # Run Pilot with large terminal size to simulate full screen display
        async with app.run_test(size=(120, 50)) as pilot:
            # 1. On Title Screen
            assert app.screen.__class__.__name__ == "TitleScreen"

            # Test Settings Screen
            await pilot.click("#btn-settings")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "SettingsScreen"
            await pilot.click("#btn-back-settings")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "TitleScreen"

            # Test How to Play Screen
            await pilot.click("#btn-how-to-play")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "HowToPlayScreen"
            await pilot.click("#btn-back-rules")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "TitleScreen"
            
            # 2. Click Practice Mode to start game
            await pilot.click("#btn-play-practice")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "BriefingScreen"

            # 3. Proceed to Interrogation
            await pilot.click("#btn-start-interrogation")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "InterrogationScreen"

            # 4. Toggle Debug Panel (F2)
            await pilot.press("f2")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "DebugPanelScreen"
            
            # Close Debug Panel
            await pilot.press("f2")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "InterrogationScreen"

            # 5. Toggle Mute (M)
            await pilot.press("m")
            await pilot.pause()

            # 6. Open Accuse Modal (A)
            await pilot.press("a")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "AccuseModalScreen"
            
            # Dismiss Accuse Modal (Esc)
            await pilot.press("escape")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "InterrogationScreen"

            # 7. Test Back to Menu from Interrogation Screen
            await pilot.click("#btn-back-menu")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "TitleScreen"

            # 8. Start game again and test Back to Menu from Briefing Screen
            await pilot.click("#btn-play-practice")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "BriefingScreen"
            await pilot.click("#btn-back-menu")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "TitleScreen"

            # 9. Test Result Screen Return to Title
            from alibi.ui.app import ResultScreen
            app.push_screen(ResultScreen(is_already_completed=True))
            await pilot.pause()
            assert app.screen.__class__.__name__ == "ResultScreen"
            await pilot.click("#btn-result-title")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "TitleScreen"

            # 10. Test Case Archive Screen Navigation
            await pilot.click("#btn-archive")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "ArchiveScreen"
            await pilot.click("#btn-back-archive")
            await pilot.pause()
            assert app.screen.__class__.__name__ == "TitleScreen"

    asyncio.run(_async_test())

def test_ui_title_pixel_animation():
    """Test that the looped noir pixel animation widget renders and cycles frames."""
    async def _async_test():
        mock_client = MagicMock()
        mock_client.get_embeddings.return_value = [0.05] * 768
        mock_client.get_installed_models.return_value = ["llama3.1:latest", "nomic-embed-text:latest"]
        mock_client.verify_models.return_value = (True, "OK")

        app = TheAlibiApp(client=mock_client, saves_path="saves/test_ui_progress.json")
        async with app.run_test(size=(120, 50)) as pilot:
            screen = app.screen
            assert screen.__class__.__name__ == "TitleScreen"

            # Check that #title-pixel-anim is mounted and rendering
            anim_widget = screen.query_one("#title-pixel-anim")
            assert anim_widget is not None
            assert hasattr(screen, "pixel_anim_idx")
            initial_idx = screen.pixel_anim_idx

            # Allow animation timer to tick (0.8s allows ~2 frame transitions at 0.35s interval)
            await pilot.pause(0.8)
            assert screen.pixel_anim_idx != initial_idx
            assert screen.pixel_anim_idx > 0

    asyncio.run(_async_test())
