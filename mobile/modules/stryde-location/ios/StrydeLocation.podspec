Pod::Spec.new do |s|
  s.name           = 'StrydeLocation'
  s.version        = '0.1.0'
  s.summary        = 'Native GPS run recorder for STRYDE'
  s.author         = 'STRYDE'
  s.homepage       = 'https://stryde.app'
  s.license        = 'UNLICENSED'
  s.platforms      = { :ios => '15.1' }
  s.source         = { git: '' }
  s.static_framework = true
  s.dependency 'ExpoModulesCore'
  s.source_files = '**/*.swift'
  s.swift_version = '5.9'
end
