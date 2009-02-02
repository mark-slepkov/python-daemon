# -*- coding: utf-8 -*-
#
# tests/test_lockfile.py
#
# Copyright © 2008–2009 Ben Finney <ben+python@benfinney.id.au>
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the Python Software Foundation License, version 2 or
# later as published by the Python Software Foundation.
# No warranty expressed or implied. See the file LICENSE.PSF-2 for details.

""" Unit test for lockfile module
"""

import __builtin__
import os
import sys
from StringIO import StringIO
import tempfile
import errno

import scaffold
from test_daemon import (
    FakeFileHandleStringIO,
    )

from daemon import lockfile


def setup_pidlockfile_fixtures(testcase):
    """ Set up common fixtures for PIDLockFile test cases """

    testcase.mock_outfile = StringIO()
    testcase.mock_tracker = scaffold.MockTracker(
        testcase.mock_outfile)

    testcase.mock_pidfile_path = tempfile.mktemp()

    args = dict(
        path=testcase.mock_pidfile_path,
        )

    testcase.test_instance = lockfile.PIDLockFile(**args)

    def mock_os_path_exists(path):
        if path == testcase.mock_pidfile_path:
            result = testcase.mock_pidfile_path_exists_func()
        else:
            result = False
        return result

    scaffold.mock(
        "os.path.exists",
        returns_func=mock_os_path_exists,
        tracker=testcase.mock_tracker)


class PIDLockFile_TestCase(scaffold.TestCase):
    """ Test cases for PIDLockFile class """

    def setUp(self):
        """ Set up test fixtures """
        setup_pidlockfile_fixtures(self)

    def tearDown(self):
        """ Tear down test fixtures """
        scaffold.mock_restore()

    def test_instantiate(self):
        """ New instance of PIDLockFile should be created """
        instance = self.test_instance
        self.failUnlessIsInstance(instance, lockfile.PIDLockFile)

    def test_has_specified_path(self):
        """ Should have specified path """
        instance = self.test_instance
        expect_path = self.mock_pidfile_path
        self.failUnlessEqual(expect_path, instance.path)


class PIDLockFile_is_locked_TestCase(scaffold.TestCase):
    """ Test cases for PIDLockFile class """

    def setUp(self):
        """ Set up test fixtures """
        setup_pidlockfile_fixtures(self)

    def tearDown(self):
        """ Tear down test fixtures """
        scaffold.mock_restore()

    def test_returns_true_if_pid_file(self):
        """ Should return True if PID file exists """
        instance = self.test_instance
        expect_result = True
        self.mock_pidfile_path_exists_func = (lambda: True)
        result = instance.is_locked()
        self.failUnlessEqual(expect_result, result)

    def test_returns_false_if_no_pid_file(self):
        """ Should return True if PID file does not exist """
        instance = self.test_instance
        expect_result = False
        self.mock_pidfile_path_exists_func = (lambda: False)
        result = instance.is_locked()
        self.failUnlessEqual(expect_result, result)


def setup_pidfile_fixtures(testcase):
    """ Set up common fixtures for PID file test cases """

    testcase.mock_outfile = StringIO()
    testcase.mock_tracker = scaffold.MockTracker(
        testcase.mock_outfile)

    testcase.mock_pid = 235
    testcase.mock_pidfile_name = tempfile.mktemp()
    testcase.mock_pidfile = FakeFileHandleStringIO()

    def mock_path_exists(path):
        if path == testcase.mock_pidfile_name:
            result = testcase.pidfile_exists_func(path)
        else:
            result = False
        return result

    testcase.pidfile_exists_func = (lambda p: False)

    scaffold.mock(
        "os.path.exists",
        mock_obj=mock_path_exists)

    def mock_pidfile_open_nonexist(filename, mode, buffering):
        if 'r' in mode:
            raise IOError("No such file %(filename)r" % vars())
        else:
            result = testcase.mock_pidfile
        return result

    def mock_pidfile_open_exist(filename, mode, buffering):
        pidfile = testcase.mock_pidfile
        pidfile.write("%(mock_pid)s\n" % vars(testcase))
        pidfile.seek(0)
        return pidfile

    testcase.mock_pidfile_open_nonexist = mock_pidfile_open_nonexist
    testcase.mock_pidfile_open_exist = mock_pidfile_open_exist

    testcase.pidfile_open_func = mock_pidfile_open_nonexist

    def mock_open(filename, mode=None, buffering=None):
        if filename == testcase.mock_pidfile_name:
            result = testcase.pidfile_open_func(filename, mode, buffering)
        else:
            result = FakeFileHandleStringIO()
        return result

    scaffold.mock(
        "__builtin__.file",
        returns_func=mock_open,
        tracker=testcase.mock_tracker)


class pidfile_exists_TestCase(scaffold.TestCase):
    """ Test cases for pidfile_exists function """

    def setUp(self):
        """ Set up test fixtures """
        setup_pidfile_fixtures(self)

    def tearDown(self):
        """ Tear down test fixtures """
        scaffold.mock_restore()

    def test_returns_true_when_pidfile_exists(self):
        """ Should return True when pidfile exists """
        self.pidfile_exists_func = (lambda p: True)
        result = lockfile.pidfile_exists(self.mock_pidfile_name)
        self.failUnless(result)

    def test_returns_false_when_no_pidfile_exists(self):
        """ Should return False when pidfile does not exist """
        self.pidfile_exists_func = (lambda p: False)
        result = lockfile.pidfile_exists(self.mock_pidfile_name)
        self.failIf(result)


class read_pid_from_pidfile_TestCase(scaffold.TestCase):
    """ Test cases for read_pid_from_pidfile function """

    def setUp(self):
        """ Set up test fixtures """
        setup_pidfile_fixtures(self)
        self.pidfile_open_func = self.mock_pidfile_open_exist

    def tearDown(self):
        """ Tear down test fixtures """
        scaffold.mock_restore()

    def test_opens_specified_filename(self):
        """ Should attempt to open specified pidfile filename """
        pidfile_name = self.mock_pidfile_name
        expect_mock_output = """\
            Called __builtin__.file(%(pidfile_name)r, 'r')
            """ % vars()
        dummy = lockfile.read_pid_from_pidfile(pidfile_name)
        scaffold.mock_restore()
        self.failUnlessOutputCheckerMatch(
            expect_mock_output, self.mock_outfile.getvalue())

    def test_reads_pid_from_file(self):
        """ Should read the PID from the specified file """
        pidfile_name = self.mock_pidfile_name
        expect_pid = self.mock_pid
        pid = lockfile.read_pid_from_pidfile(pidfile_name)
        scaffold.mock_restore()
        self.failUnlessEqual(expect_pid, pid)

    def test_returns_none_when_file_nonexist(self):
        """ Should return None when the PID file does not exist """
        pidfile_name = self.mock_pidfile_name
        self.pidfile_open_func = self.mock_pidfile_open_nonexist
        pid = lockfile.read_pid_from_pidfile(pidfile_name)
        scaffold.mock_restore()
        self.failUnlessIs(None, pid)


class remove_existing_pidfile_TestCase(scaffold.TestCase):
    """ Test cases for remove_existing_pidfile function """

    def setUp(self):
        """ Set up test fixtures """
        setup_pidfile_fixtures(self)
        self.pidfile_open_func = self.mock_pidfile_open_exist

        scaffold.mock(
            "os.remove",
            tracker=self.mock_tracker)

    def tearDown(self):
        """ Tear down test fixtures """
        scaffold.mock_restore()

    def test_removes_specified_filename(self):
        """ Should attempt to remove specified PID file filename """
        pidfile_name = self.mock_pidfile_name
        expect_mock_output = """\
            Called os.remove(%(pidfile_name)r)
            """ % vars()
        lockfile.remove_existing_pidfile(pidfile_name)
        scaffold.mock_restore()
        self.failUnlessOutputCheckerMatch(
            expect_mock_output, self.mock_outfile.getvalue())

    def test_ignores_file_not_exist_error(self):
        """ Should ignore error if file does not exist """
        pidfile_name = self.mock_pidfile_name
        mock_error = OSError(errno.ENOENT, "Not there", pidfile_name)
        os.remove.mock_raises = mock_error
        expect_mock_output = """\
            Called os.remove(%(pidfile_name)r)
            """ % vars()
        lockfile.remove_existing_pidfile(pidfile_name)
        scaffold.mock_restore()
        self.failUnlessOutputCheckerMatch(
            expect_mock_output, self.mock_outfile.getvalue())

    def test_propagates_arbitrary_oserror(self):
        """ Should propagate any OSError other than ENOENT """
        pidfile_name = self.mock_pidfile_name
        mock_error = OSError(errno.EACCES, "Denied", pidfile_name)
        os.remove.mock_raises = mock_error
        self.failUnlessRaises(
            mock_error.__class__,
            lockfile.remove_existing_pidfile,
            pidfile_name)


class write_pid_to_pidfile_TestCase(scaffold.TestCase):
    """ Test cases for write_pid_to_pidfile function """

    def setUp(self):
        """ Set up test fixtures """
        setup_pidfile_fixtures(self)
        self.pidfile_open_func = self.mock_pidfile_open_nonexist

        scaffold.mock(
            "os.getpid",
            returns=self.mock_pid,
            tracker=self.mock_tracker)

    def tearDown(self):
        """ Tear down test fixtures """
        scaffold.mock_restore()

    def test_opens_specified_filename(self):
        """ Should attempt to open specified PID file filename """
        pidfile_name = self.mock_pidfile_name
        expect_mock_output = """\
            Called __builtin__.file(%(pidfile_name)r, 'w')
            ...
            """ % vars()
        lockfile.write_pid_to_pidfile(pidfile_name)
        scaffold.mock_restore()
        self.failUnlessOutputCheckerMatch(
            expect_mock_output, self.mock_outfile.getvalue())

    def test_writes_pid_to_file(self):
        """ Should write the current PID to the specified file """
        pidfile_name = self.mock_pidfile_name
        expect_line = "%(mock_pid)d\n" % vars(self)
        expect_mock_output = """\
            ...
            Called 
            """ % vars()
        lockfile.write_pid_to_pidfile(pidfile_name)
        scaffold.mock_restore()
        self.failUnlessEqual(expect_line, self.mock_pidfile.getvalue())
