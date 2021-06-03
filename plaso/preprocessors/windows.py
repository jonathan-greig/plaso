# -*- coding: utf-8 -*-
"""This file contains preprocessors for Windows."""

from plaso.containers import artifacts
from plaso.lib import errors
from plaso.preprocessors import interface
from plaso.preprocessors import logger
from plaso.preprocessors import manager
from plaso.winnt import time_zones


class WindowsEnvironmentVariableArtifactPreprocessorPlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """Windows environment variable artifact preprocessor plugin interface."""

  _NAME = None

  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, str):
      raise errors.PreProcessFail(
          'Unsupported Windows Registry value type: {0!s} for '
          'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=self._NAME, value=value_data)

    try:
      logger.debug('setting environment variable: {0:s} to: "{1:s}"'.format(
          self._NAME, value_data))
      mediator.knowledge_base.AddEnvironmentVariable(environment_variable)
    except KeyError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to set environment variable: {0:s} in knowledge base.'.format(
              self._NAME))


class WindowsPathEnvironmentVariableArtifactPreprocessorPlugin(
    interface.FileSystemArtifactPreprocessorPlugin):
  """Windows path environment variable plugin interface."""

  _NAME = None

  def _ParsePathSpecification(
      self, mediator, searcher, file_system, path_specification,
      path_separator):
    """Parses artifact file system data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
      searcher (dfvfs.FileSystemSearcher): file system searcher to preprocess
          the file system.
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      path_specification (dfvfs.PathSpec): path specification that contains
          the artifact value data.
      path_separator (str): path segment separator.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    relative_path = searcher.GetRelativePath(path_specification)
    if not relative_path:
      raise errors.PreProcessFail(
          'Unable to read: {0:s} with error: missing relative path'.format(
              self.ARTIFACT_DEFINITION_NAME))

    if path_separator != file_system.PATH_SEPARATOR:
      relative_path_segments = file_system.SplitPath(relative_path)
      relative_path = '{0:s}{1:s}'.format(
          path_separator, path_separator.join(relative_path_segments))

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=self._NAME, value=relative_path)

    try:
      logger.debug('setting environment variable: {0:s} to: "{1:s}"'.format(
          self._NAME, relative_path))
      mediator.knowledge_base.AddEnvironmentVariable(environment_variable)
    except KeyError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to set environment variable: {0:s} in knowledge base.'.format(
              self._NAME))


class WindowsAllUsersAppDataKnowledgeBasePlugin(
    interface.KnowledgeBasePreprocessorPlugin):
  """The allusersdata knowledge base value plugin.

  The allusersdata value is needed for the expansion of
  %%environ_allusersappdata%% in artifact definitions.
  """

  def Collect(self, mediator):
    """Collects values from the knowledge base.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """
    environment_variable = mediator.knowledge_base.GetEnvironmentVariable(
        'programdata')
    allusersappdata = getattr(environment_variable, 'value', None)

    if not allusersappdata:
      environment_variable = mediator.knowledge_base.GetEnvironmentVariable(
          'allusersprofile')
      allusersdata = getattr(environment_variable, 'value', None)

      if allusersdata:
        allusersappdata = '\\'.join([allusersdata, 'Application Data'])

    if allusersappdata:
      environment_variable = artifacts.EnvironmentVariableArtifact(
          case_sensitive=False, name='allusersappdata', value=allusersappdata)

      try:
        logger.debug('setting environment variable: {0:s} to: "{1:s}"'.format(
            'allusersappdata', allusersappdata))
        mediator.knowledge_base.AddEnvironmentVariable(environment_variable)
      except KeyError:
        mediator.ProducePreprocessingWarning(
            self.__class__.__name__,
            ('Unable to set environment variable: %AllUsersAppData% in '
             'knowledge base.'))


class WindowsAllUsersProfileEnvironmentVariablePlugin(
    WindowsEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %AllUsersProfile% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEnvironmentVariableAllUsersProfile'

  _NAME = 'allusersprofile'


class WindowsAllUsersAppProfileKnowledgeBasePlugin(
    interface.KnowledgeBasePreprocessorPlugin):
  """The allusersprofile knowledge base value plugin.

  The allusersprofile value is needed for the expansion of
  %%environ_allusersappprofile%% in artifact definitions.

  It is derived from %ProgramData% for versions of Windows, Vista and later,
  that do not define %AllUsersProfile%.
  """

  def Collect(self, mediator):
    """Collects values from the knowledge base.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """
    environment_variable = mediator.knowledge_base.GetEnvironmentVariable(
        'allusersprofile')
    allusersprofile = getattr(environment_variable, 'value', None)

    if not allusersprofile:
      environment_variable = mediator.knowledge_base.GetEnvironmentVariable(
          'programdata')
      allusersprofile = getattr(environment_variable, 'value', None)

      if allusersprofile:
        environment_variable = artifacts.EnvironmentVariableArtifact(
            case_sensitive=False, name='allusersprofile', value=allusersprofile)

        try:
          logger.debug('setting environment variable: {0:s} to: "{1:s}"'.format(
              'allusersprofile', allusersprofile))
          mediator.knowledge_base.AddEnvironmentVariable(environment_variable)
        except KeyError:
          mediator.ProducePreprocessingWarning(
              self.__class__.__name__,
              ('Unable to set environment variable: %AllUsersProfile% in '
               'knowledge base.'))


class WindowsAvailableTimeZonesPlugin(
    interface.WindowsRegistryKeyArtifactPreprocessorPlugin):
  """The Windows available time zones plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsAvailableTimeZones'

  def _ParseKey(self, mediator, registry_key, value_name):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the Windows Registry value.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    time_zone_artifact = artifacts.TimeZoneArtifact(name=registry_key.name)

    try:
      mediator.knowledge_base.AddAvailableTimeZone(time_zone_artifact)
    except KeyError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to set time zone in knowledge base.')


class WindowsCodepagePlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows codepage plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsCodePage'

  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, str):
      raise errors.PreProcessFail(
          'Unsupported Windows Registry value type: {0!s} for '
          'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    # Map the Windows code page name to a Python equivalent name.
    codepage = 'cp{0:s}'.format(value_data)

    if not mediator.knowledge_base.codepage:
      try:
        mediator.knowledge_base.SetCodepage(codepage)
      except ValueError:
        mediator.ProducePreprocessingWarning(
            self.ARTIFACT_DEFINITION_NAME,
            'Unable to set codepage in knowledge base.')


class WindowsHostnamePlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows hostname plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsComputerName'

  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, str):
      if not hasattr(value_data, '__iter__'):
        raise errors.PreProcessFail(
            'Unsupported Windows Registry value type: {0!s} for '
            'artifact: {1:s}.'.format(
                type(value_data), self.ARTIFACT_DEFINITION_NAME))

      # If the value data is a multi string only use the first string.
      value_data = value_data[0]

    if not mediator.knowledge_base.GetHostname():
      hostname_artifact = artifacts.HostnameArtifact(name=value_data)
      mediator.knowledge_base.SetHostname(hostname_artifact)


class WindowsProgramDataEnvironmentVariablePlugin(
    WindowsEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %ProgramData% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEnvironmentVariableProgramData'

  _NAME = 'programdata'


class WindowsProgramDataKnowledgeBasePlugin(
    interface.KnowledgeBasePreprocessorPlugin):
  """The programdata knowledge base value plugin.

  The programdata value is needed for the expansion of %%environ_programdata%%
  in artifact definitions.

  It is derived from %AllUsersProfile% for versions of Windows prior to Vista
  that do not define %ProgramData%.
  """

  def Collect(self, mediator):
    """Collects values from the knowledge base.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """
    environment_variable = mediator.knowledge_base.GetEnvironmentVariable(
        'programdata')
    allusersprofile = getattr(environment_variable, 'value', None)

    if not allusersprofile:
      environment_variable = mediator.knowledge_base.GetEnvironmentVariable(
          'allusersprofile')
      allusersprofile = getattr(environment_variable, 'value', None)

      if allusersprofile:
        environment_variable = artifacts.EnvironmentVariableArtifact(
            case_sensitive=False, name='programdata', value=allusersprofile)

        try:
          logger.debug('setting environment variable: {0:s} to: "{1:s}"'.format(
              'programdata', allusersprofile))
          mediator.knowledge_base.AddEnvironmentVariable(environment_variable)
        except KeyError:
          mediator.ProducePreprocessingWarning(
              self.__class__.__name__,
              ('Unable to set environment variable: %ProgramData% in '
               'knowledge base.'))


class WindowsProgramFilesEnvironmentVariablePlugin(
    WindowsEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %ProgramFiles% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEnvironmentVariableProgramFiles'

  _NAME = 'programfiles'


class WindowsProgramFilesX86EnvironmentVariablePlugin(
    WindowsEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %ProgramFilesX86% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEnvironmentVariableProgramFilesX86'

  _NAME = 'programfilesx86'


class WindowsSystemProductPlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows system product information plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsProductName'

  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, str):
      raise errors.PreProcessFail(
          'Unsupported Windows Registry value type: {0!s} for '
          'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    if not mediator.knowledge_base.GetValue('operating_system_product'):
      mediator.knowledge_base.SetValue('operating_system_product', value_data)


class WindowsSystemRootEnvironmentVariablePlugin(
    WindowsPathEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %SystemRoot% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEnvironmentVariableSystemRoot'

  _NAME = 'systemroot'


class WindowsSystemVersionPlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows system version information plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsCurrentVersion'

  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, str):
      raise errors.PreProcessFail(
          'Unsupported Windows Registry value type: {0!s} for '
          'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    if not mediator.knowledge_base.GetValue('operating_system_version'):
      mediator.knowledge_base.SetValue('operating_system_version', value_data)


class WindowsTimeZonePlugin(
    interface.WindowsRegistryValueArtifactPreprocessorPlugin):
  """The Windows time zone plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsTimezone'

  def _ParseValueData(self, mediator, value_data):
    """Parses Windows Registry value data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
      value_data (object): Windows Registry value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not isinstance(value_data, str):
      raise errors.PreProcessFail(
          'Unsupported Windows Registry value type: {0!s} for '
          'artifact: {1:s}.'.format(
              type(value_data), self.ARTIFACT_DEFINITION_NAME))

    # Map the Windows time zone name to a Python equivalent name.
    lookup_key = value_data.replace(' ', '')

    time_zone = time_zones.TIME_ZONES.get(lookup_key, value_data)
    # TODO: check if time zone is set in knowledge base.
    if time_zone:
      try:
        # Catch and warn about unsupported preprocessor plugin.
        mediator.knowledge_base.SetTimeZone(time_zone)
      except ValueError:
        mediator.ProducePreprocessingWarning(
            self.ARTIFACT_DEFINITION_NAME,
            'Unable to map: "{0:s}" to time zone'.format(value_data))


class WindowsUserAccountsPlugin(
    interface.WindowsRegistryKeyArtifactPreprocessorPlugin):
  """The Windows user account plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsRegistryProfiles'

  def _GetUsernameFromProfilePath(self, path):
    """Retrieves the username from a Windows profile path.

    Trailing path path segment are ignored.

    Args:
      path (str): a Windows path with '\\' as path segment separator.

    Returns:
      str: basename which is the last path segment.
    """
    # Strip trailing key separators.
    while path and path[-1] == '\\':
      path = path[:-1]

    if path:
      _, _, path = path.rpartition('\\')
    return path

  def _ParseKey(self, mediator, registry_key, value_name):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      value_name (str): name of the Windows Registry value.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    user_account = artifacts.UserAccountArtifact(
        identifier=registry_key.name, path_separator='\\')

    registry_value = registry_key.GetValueByName('ProfileImagePath')
    if registry_value:
      profile_path = registry_value.GetDataAsObject()
      username = self._GetUsernameFromProfilePath(profile_path)

      user_account.user_directory = profile_path or None
      user_account.username = username or None

    try:
      mediator.knowledge_base.AddUserAccount(user_account)
    except KeyError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          ('Unable to add user account: "{0!s}" to knowledge '
           'base').format(username))


class WindowsWinDirEnvironmentVariablePlugin(
    WindowsPathEnvironmentVariableArtifactPreprocessorPlugin):
  """The Windows %WinDir% environment variable plugin."""

  ARTIFACT_DEFINITION_NAME = 'WindowsEnvironmentVariableWinDir'

  _NAME = 'windir'


manager.PreprocessPluginsManager.RegisterPlugins([
    WindowsAllUsersAppDataKnowledgeBasePlugin,
    WindowsAllUsersProfileEnvironmentVariablePlugin,
    WindowsAllUsersAppProfileKnowledgeBasePlugin,
    WindowsAvailableTimeZonesPlugin,
    WindowsCodepagePlugin, WindowsHostnamePlugin,
    WindowsProgramDataEnvironmentVariablePlugin,
    WindowsProgramDataKnowledgeBasePlugin,
    WindowsProgramFilesEnvironmentVariablePlugin,
    WindowsProgramFilesX86EnvironmentVariablePlugin,
    WindowsSystemProductPlugin, WindowsSystemRootEnvironmentVariablePlugin,
    WindowsSystemVersionPlugin, WindowsTimeZonePlugin,
    WindowsWinDirEnvironmentVariablePlugin, WindowsUserAccountsPlugin])
