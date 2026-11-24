import { router } from 'expo-router';
import { Pressable, ScrollView, Text, View } from 'react-native';

import { useCompleteSession, usePlan } from '../../api/hooks';
import { Card, Loading, Screen } from '../../components/ui';
import { colors, formatDuration, type } from '../../theme';

const DAY = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

export default function Train() {
  const plan = usePlan();
  const complete = useCompleteSession();
  if (plan.isLoading) return <Loading />;
  const p = plan.data;
  const today = new Date().toLocaleDateString('en-CA'); // local YYYY-MM-DD

  if (!p) {
    return (
      <Screen>
        <View style={{ padding: 20 }}>
          <Text style={type.h1}>Train</Text>
          <Text style={[type.small, { marginTop: 8 }]}>
            Lose a title and STRYDE builds a week of training aimed at the rematch. Open any route you've run and tap "Plan my comeback".
          </Text>
        </View>
      </Screen>
    );
  }
  const done = p.sessions.filter((s) => s.completed_at).length;

  return (
    <Screen>
      <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 120 }}>
        <Text style={type.kicker}>Comeback plan</Text>
        <Text style={[type.h1, { marginTop: 6 }]}>{p.title}</Text>
        <View style={{ flexDirection: 'row', gap: 10, marginTop: 16 }}>
          <Card style={{ flex: 1, padding: 12 }}>
            <Text style={type.small}>Goal</Text>
            <Text style={type.h3}>&lt; {formatDuration(p.goal_time_s)}</Text>
          </Card>
          <Card style={{ flex: 1, padding: 12 }}>
            <Text style={type.small}>Attempt</Text>
            <Text style={type.h3}>{p.attempt_on ? new Date(p.attempt_on + 'T12:00:00').toLocaleDateString(undefined, { weekday: 'long' }) : '—'}</Text>
          </Card>
          <Card style={{ flex: 1, padding: 12 }}>
            <Text style={type.small}>Done</Text>
            <Text style={type.h3}>
              {done} of {p.sessions.filter((s) => s.kind !== 'rest').length}
            </Text>
          </Card>
        </View>

        <Text style={[type.h2, { marginTop: 22, marginBottom: 8 }]}>This week</Text>
        {p.sessions.map((s) => {
          const isToday = s.date === today;
          const isGoal = s.kind === 'attempt';
          return (
            <Pressable
              key={s.id}
              onPress={() => {
                if (isGoal && p.route) router.push({ pathname: '/run', params: { route: p.route } });
                else if (!s.completed_at && s.kind !== 'rest') complete.mutate(s.id);
              }}
              style={{
                flexDirection: 'row',
                alignItems: 'center',
                gap: 12,
                padding: 12,
                borderRadius: 16,
                borderWidth: 1,
                borderColor: isToday ? 'rgba(215,255,58,0.4)' : isGoal ? 'rgba(255,200,61,0.35)' : 'transparent',
                backgroundColor: isToday ? 'rgba(215,255,58,0.08)' : isGoal ? 'rgba(255,200,61,0.07)' : 'transparent',
                marginBottom: 2,
              }}
            >
              <Text style={{ width: 14, color: colors.muted, fontWeight: '700' }}>{DAY[new Date(s.date + 'T12:00:00').getDay()]}</Text>
              <View style={{ flex: 1 }}>
                <Text style={[type.h3, s.completed_at ? { color: colors.muted } : null]}>
                  {s.title}
                  {s.minutes ? ` · ${s.minutes} min` : ''}
                </Text>
                <Text style={type.small}>{s.detail}</Text>
              </View>
              <View
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 14,
                  backgroundColor: s.completed_at ? colors.volt : 'transparent',
                  borderWidth: s.completed_at ? 0 : 2,
                  borderColor: isToday ? colors.volt : colors.surface3,
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {s.completed_at ? <Text style={{ color: colors.bg, fontWeight: '900' }}>✓</Text> : isGoal ? <Text style={{ color: colors.gold }}>♛</Text> : null}
              </View>
            </Pressable>
          );
        })}
        <Text style={[type.small, { marginTop: 12, fontSize: 11.5 }]}>Plans are general guidance, not medical advice.</Text>
      </ScrollView>
    </Screen>
  );
}
