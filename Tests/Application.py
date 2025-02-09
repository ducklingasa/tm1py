import configparser
import os
import random
import unittest

from _datetime import datetime

from TM1py import TM1Service, Element, ElementAttribute, Hierarchy, Dimension, Cube, NativeView, AnonymousSubset, \
    Subset, Process, Chore, ChoreStartTime, ChoreFrequency, ChoreTask
from TM1py.Objects.Application import CubeApplication, ApplicationTypes, ChoreApplication, DimensionApplication, \
    FolderApplication, LinkApplication, ProcessApplication, SubsetApplication, ViewApplication

config = configparser.ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini'))

# Hard coded stuff
PREFIX = 'TM1py_Tests_Applications_'
TM1PY_APP_FOLDER = PREFIX + "RootFolder"
APPLICATION_NAME = PREFIX + "Application"
CUBE_NAME = PREFIX + "Cube"
VIEW_NAME = PREFIX + "View"
SUBSET_NAME = PREFIX + "Subset"
PROCESS_NAME = PREFIX + "Process"
CHORE_NAME = PREFIX + "Chore"
FOLDER_NAME = PREFIX + "Folder"
LINK_NAME = PREFIX + "Link"
DOCUMENT_NAME = PREFIX + "Document"
DIMENSION_NAMES = [
    PREFIX + 'Dimension1',
    PREFIX + 'Dimension2',
    PREFIX + 'Dimension3']


class TestDataMethods(unittest.TestCase):
    tm1 = None

    # Setup Cubes, Dimensions and Subsets
    @classmethod
    def setup_class(cls):
        # Connection to TM1
        cls.tm1 = TM1Service(**config['tm1srv01'])

    @classmethod
    def setUpClass(cls) -> None:
        # Build Dimensions
        for dimension_name in DIMENSION_NAMES:
            elements = [Element('Element {}'.format(str(j)), 'Numeric') for j in range(1, 1001)]
            element_attributes = [ElementAttribute("Attr1", "String"),
                                  ElementAttribute("Attr2", "Numeric"),
                                  ElementAttribute("Attr3", "Numeric")]
            hierarchy = Hierarchy(dimension_name=dimension_name,
                                  name=dimension_name,
                                  elements=elements,
                                  element_attributes=element_attributes)
            dimension = Dimension(dimension_name, [hierarchy])
            if cls.tm1.dimensions.exists(dimension.name):
                cls.tm1.dimensions.update(dimension)
            else:
                cls.tm1.dimensions.create(dimension)

        # Build Cube
        cube = Cube(CUBE_NAME, DIMENSION_NAMES)
        if not cls.tm1.cubes.exists(CUBE_NAME):
            cls.tm1.cubes.create(cube)

        # Build cube view
        view = NativeView(
            cube_name=CUBE_NAME,
            view_name=VIEW_NAME,
            suppress_empty_columns=True,
            suppress_empty_rows=True)
        view.add_row(
            dimension_name=DIMENSION_NAMES[0],
            subset=AnonymousSubset(
                dimension_name=DIMENSION_NAMES[0],
                expression='{[' + DIMENSION_NAMES[0] + '].Members}'))
        view.add_row(
            dimension_name=DIMENSION_NAMES[1],
            subset=AnonymousSubset(
                dimension_name=DIMENSION_NAMES[1],
                expression='{[' + DIMENSION_NAMES[1] + '].Members}'))
        view.add_column(
            dimension_name=DIMENSION_NAMES[2],
            subset=AnonymousSubset(
                dimension_name=DIMENSION_NAMES[2],
                expression='{[' + DIMENSION_NAMES[2] + '].Members}'))
        if not cls.tm1.cubes.views.exists(CUBE_NAME, view.name, private=False):
            cls.tm1.cubes.views.create(
                view=view,
                private=False)

        # Build subset
        subset = Subset(SUBSET_NAME, DIMENSION_NAMES[0], DIMENSION_NAMES[0], None, None, ["Element 1"])
        if cls.tm1.dimensions.hierarchies.subsets.exists(
                subset.name,
                subset.dimension_name,
                subset.hierarchy_name,
                False):
            cls.tm1.dimensions.hierarchies.subsets.delete(
                subset.name,
                subset.dimension_name,
                subset.hierarchy_name,
                False)
        cls.tm1.dimensions.hierarchies.subsets.create(subset, False)

        # Build process
        p1 = Process(name=PROCESS_NAME)
        p1.add_parameter('pRegion', 'pRegion (String)', value='US')
        if cls.tm1.processes.exists(p1.name):
            cls.tm1.processes.delete(p1.name)
        cls.tm1.processes.create(p1)

        # Build chore
        c1 = Chore(
            name=CHORE_NAME,
            start_time=ChoreStartTime(datetime.now().year, datetime.now().month, datetime.now().day,
                                      datetime.now().hour, datetime.now().minute, datetime.now().second),
            dst_sensitivity=False,
            active=True,
            execution_mode=Chore.MULTIPLE_COMMIT,
            frequency=ChoreFrequency(
                days=int(random.uniform(0, 355)),
                hours=int(random.uniform(0, 23)),
                minutes=int(random.uniform(0, 59)),
                seconds=int(random.uniform(0, 59))),
            tasks=[ChoreTask(0, PROCESS_NAME, parameters=[{'Name': 'pRegion', 'Value': 'UK'}])])
        cls.tm1.chores.create(c1)

        # create Folder
        app = FolderApplication("", TM1PY_APP_FOLDER)
        cls.tm1.applications.create(application=app, private=False)

    @classmethod
    def tearDownClass(cls) -> None:
        # delete view
        cls.tm1.cubes.views.delete(CUBE_NAME, VIEW_NAME, False)
        # delete cube
        cls.tm1.cubes.delete(CUBE_NAME)
        # delete dimensions
        for dimension_name in DIMENSION_NAMES:
            cls.tm1.dimensions.delete(dimension_name)
        # delete chore
        cls.tm1.chores.delete(CHORE_NAME)
        # delete process
        cls.tm1.processes.delete(PROCESS_NAME)
        # delete folder
        cls.tm1.applications.delete(
            path="",
            application_type=ApplicationTypes.FOLDER,
            application_name=TM1PY_APP_FOLDER,
            private=False)

    def test_cube_application(self):
        app = CubeApplication(TM1PY_APP_FOLDER, APPLICATION_NAME, CUBE_NAME)
        self.tm1.applications.create(application=app, private=False)
        app_retrieved = self.tm1.applications.get(app.path, app.application_type, app.name, private=False)
        self.assertEqual(app, app_retrieved)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.CUBE, private=False)
        self.assertTrue(exists)

        self.tm1.applications.delete(app.path, app.application_type, app.name, private=False)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.CUBE, private=False)
        self.assertFalse(exists)

    def test_chore_application(self):
        app = ChoreApplication(TM1PY_APP_FOLDER, APPLICATION_NAME, CHORE_NAME)
        self.tm1.applications.create(application=app, private=False)
        app_retrieved = self.tm1.applications.get(app.path, app.application_type, app.name, private=False)
        self.assertEqual(app, app_retrieved)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.CHORE, private=False)
        self.assertTrue(exists)

        self.tm1.applications.delete(app.path, app.application_type, app.name, private=False)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.CHORE, private=False)
        self.assertFalse(exists)

    def test_dimension_application(self):
        app = DimensionApplication(TM1PY_APP_FOLDER, APPLICATION_NAME, DIMENSION_NAMES[0])
        self.tm1.applications.create(application=app, private=False)
        app_retrieved = self.tm1.applications.get(app.path, app.application_type, app.name, private=False)
        self.assertEqual(app, app_retrieved)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.DIMENSION, private=False)
        self.assertTrue(exists)

        self.tm1.applications.delete(app.path, app.application_type, app.name, private=False)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.DIMENSION, private=False)
        self.assertFalse(exists)

    def test_folder_application(self):
        app = FolderApplication(TM1PY_APP_FOLDER, "not_relevant")
        self.tm1.applications.create(application=app, private=False)
        app_retrieved = self.tm1.applications.get(app.path, app.application_type, app.name, private=False)
        self.assertEqual(app, app_retrieved)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.FOLDER, private=False)
        self.assertTrue(exists)

        self.tm1.applications.delete(app.path, app.application_type, app.name, private=False)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.FOLDER, private=False)
        self.assertFalse(exists)

    def test_link_application(self):
        app = LinkApplication(TM1PY_APP_FOLDER, APPLICATION_NAME, LINK_NAME)
        self.tm1.applications.create(application=app, private=False)
        app_retrieved = self.tm1.applications.get(app.path, app.application_type, app.name, private=False)
        self.assertEqual(app, app_retrieved)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.LINK, private=False)
        self.assertTrue(exists)

        self.tm1.applications.delete(app.path, app.application_type, app.name, private=False)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.LINK, private=False)
        self.assertFalse(exists)

    def test_process_application(self):
        app = ProcessApplication(TM1PY_APP_FOLDER, APPLICATION_NAME, PROCESS_NAME)
        self.tm1.applications.create(application=app, private=False)
        app_retrieved = self.tm1.applications.get(app.path, app.application_type, app.name, private=False)
        self.assertEqual(app, app_retrieved)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.PROCESS, private=False)
        self.assertTrue(exists)

        self.tm1.applications.delete(app.path, app.application_type, app.name, private=False)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.PROCESS, private=False)
        self.assertFalse(exists)

    def test_subset_application(self):
        app = SubsetApplication(TM1PY_APP_FOLDER, APPLICATION_NAME, DIMENSION_NAMES[0], DIMENSION_NAMES[0], SUBSET_NAME)
        self.tm1.applications.create(application=app, private=False)
        app_retrieved = self.tm1.applications.get(app.path, app.application_type, app.name, private=False)
        self.assertEqual(app, app_retrieved)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.SUBSET, private=False)
        self.assertTrue(exists)

        self.tm1.applications.delete(app.path, app.application_type, app.name, private=False)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.SUBSET, private=False)
        self.assertFalse(exists)

    def test_view_application(self):
        app = ViewApplication(TM1PY_APP_FOLDER, APPLICATION_NAME, CUBE_NAME, VIEW_NAME)
        self.tm1.applications.create(application=app, private=False)
        app_retrieved = self.tm1.applications.get(app.path, app.application_type, app.name, private=False)
        self.assertEqual(app, app_retrieved)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.VIEW, private=False)
        self.assertTrue(exists)

        self.tm1.applications.delete(app.path, app.application_type, app.name, private=False)
        exists = self.tm1.applications.exists(
            app.path, name=app.name, application_type=ApplicationTypes.VIEW, private=False)
        self.assertFalse(exists)
