def test_student_dashboard_exposes_redesigned_visual_sections(logged_in_student):
    response = logged_in_student.get("/student")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "app-shell" in page
    assert "welcome-panel" in page
    assert "feature-grid" in page
    assert "status-panel" in page


def test_shared_layout_exposes_responsive_navigation(logged_in_student):
    response = logged_in_student.get("/student")
    page = response.get_data(as_text=True)

    assert 'class="site-header"' in page
    assert 'class="site-nav"' in page
    assert 'name="viewport"' in page
