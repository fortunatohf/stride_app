import { Tabs } from 'expo-router';
import { Text, View, type ColorValue } from 'react-native';

import { colors } from '../../theme';

const icon = (glyph: string) =>
  function TabIcon({ color }: { color: ColorValue }) {
    return <Text style={{ color, fontSize: 18 }}>{glyph}</Text>;
  };

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: { backgroundColor: 'rgba(14,15,19,0.96)', borderTopColor: colors.line, height: 88, paddingTop: 8 },
        tabBarActiveTintColor: colors.text,
        tabBarInactiveTintColor: colors.muted2,
        tabBarLabelStyle: { fontSize: 10.5, fontWeight: '600' },
      }}
    >
      <Tabs.Screen name="index" options={{ title: 'Home', tabBarIcon: icon('⌂') }} />
      <Tabs.Screen name="routes" options={{ title: 'Routes', tabBarIcon: icon('◫') }} />
      <Tabs.Screen
        name="run"
        options={{
          title: '',
          tabBarIcon: () => (
            <View style={{ width: 58, height: 58, borderRadius: 29, backgroundColor: colors.volt, marginTop: 4, alignItems: 'center', justifyContent: 'center' }}>
              <Text style={{ fontSize: 24, color: colors.bg, fontWeight: '800' }}>▶</Text>
            </View>
          ),
        }}
      />
      <Tabs.Screen name="league" options={{ title: 'League', tabBarIcon: icon('♛') }} />
      <Tabs.Screen name="train" options={{ title: 'Train', tabBarIcon: icon('▦') }} />
    </Tabs>
  );
}
