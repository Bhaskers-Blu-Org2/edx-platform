"""Acceptance tests for LMS-hosted Programs pages"""
from nose.plugins.attrib import attr

from common.test.acceptance.fixtures.catalog import CatalogFixture, CatalogConfigMixin
from common.test.acceptance.fixtures.programs import ProgramsFixture, ProgramsConfigMixin
from common.test.acceptance.fixtures.course import CourseFixture
from common.test.acceptance.tests.helpers import UniqueCourseTest
from common.test.acceptance.pages.lms.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.programs import ProgramListingPage, ProgramDetailsPage
from openedx.core.djangoapps.catalog.tests import factories as catalog_factories
from openedx.core.djangoapps.programs.tests import factories as program_factories


class ProgramPageBase(ProgramsConfigMixin, CatalogConfigMixin, UniqueCourseTest):
    """Base class used for program listing page tests."""
    def setUp(self):
        super(ProgramPageBase, self).setUp()

        self.set_programs_api_configuration(is_enabled=True)

        self.programs = [catalog_factories.Program() for __ in range(3)]
        self.course_run = catalog_factories.CourseRun(key=self.course_id)
        self.stub_catalog_api()

    def create_program(self, program_id=None, course_id=None):
        """DRY helper for creating test program data."""
        course_id = course_id if course_id else self.course_id

        run_mode = program_factories.RunMode(course_key=course_id)
        course_code = program_factories.CourseCode(run_modes=[run_mode])
        org = program_factories.Organization(key=self.course_info['org'])

        if program_id:
            program = program_factories.Program(
                id=program_id,
                status='active',
                organizations=[org],
                course_codes=[course_code]
            )
        else:
            program = program_factories.Program(
                status='active',
                organizations=[org],
                course_codes=[course_code]
            )

        return program

    def stub_programs_api(self, programs, is_list=True):
        """Stub out the programs API with fake data."""
        ProgramsFixture().install_programs(programs, is_list=is_list)

    def stub_catalog_api(self):
        """Stub out the catalog API's program and course run endpoints."""
        self.set_catalog_configuration(is_enabled=True)
        CatalogFixture().install_programs(self.programs)
        CatalogFixture().install_course_run(self.course_run)

    def auth(self, enroll=True):
        """Authenticate, enrolling the user in the configured course if requested."""
        CourseFixture(**self.course_info).install()

        course_id = self.course_id if enroll else None
        AutoAuthPage(self.browser, course_id=course_id).visit()


class ProgramListingPageTest(ProgramPageBase):
    """Verify user-facing behavior of the program listing page."""
    def setUp(self):
        super(ProgramListingPageTest, self).setUp()

        self.listing_page = ProgramListingPage(self.browser)

    def test_no_enrollments(self):
        """Verify that no cards appear when the user has no enrollments."""
        program = self.create_program()
        self.stub_programs_api([program])
        self.auth(enroll=False)

        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertFalse(self.listing_page.are_cards_present)

    def test_no_programs(self):
        """
        Verify that no cards appear when the user has enrollments
        but none are included in an active program.
        """
        course_id = self.course_id.replace(
            self.course_info['run'],
            'other_run'
        )

        program = self.create_program(course_id=course_id)
        self.stub_programs_api([program])
        self.auth()

        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertFalse(self.listing_page.are_cards_present)

    def test_enrollments_and_programs(self):
        """
        Verify that cards appear when the user has enrollments
        which are included in at least one active program.
        """
        program = self.create_program()
        self.stub_programs_api([program])
        self.auth()

        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertTrue(self.listing_page.are_cards_present)


@attr('a11y')
class ProgramListingPageA11yTest(ProgramPageBase):
    """Test program listing page accessibility."""
    def setUp(self):
        super(ProgramListingPageA11yTest, self).setUp()

        self.listing_page = ProgramListingPage(self.browser)

        program = self.create_program()
        self.stub_programs_api([program])

    def test_empty_a11y(self):
        """Test a11y of the page's empty state."""
        self.auth(enroll=False)
        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertFalse(self.listing_page.are_cards_present)
        self.listing_page.a11y_audit.check_for_accessibility_errors()

    def test_cards_a11y(self):
        """Test a11y when program cards are present."""
        self.auth()
        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertTrue(self.listing_page.are_cards_present)
        self.listing_page.a11y_audit.check_for_accessibility_errors()


@attr('a11y')
class ProgramDetailsPageA11yTest(ProgramPageBase):
    """Test program details page accessibility."""
    def setUp(self):
        super(ProgramDetailsPageA11yTest, self).setUp()

        self.details_page = ProgramDetailsPage(self.browser)

        program = self.create_program(program_id=self.details_page.program_id)
        self.stub_programs_api([program], is_list=False)

    def test_a11y(self):
        """Test the page's a11y compliance."""
        self.auth()
        self.details_page.visit()
        self.details_page.a11y_audit.check_for_accessibility_errors()
