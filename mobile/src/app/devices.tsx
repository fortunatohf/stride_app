import * as DocumentPicker from 'expo-document-picker';
import { router } from 'expo-router';
import * as WebBrowser from 'expo-web-browser';
import { useState } from 'react';
import { Platform, ScrollView, Switch, Text, View } from 'react-native';

import { api, signOut } from '../api/client';
import { useIntegrations, useMe, useUpdateMe } from '../api/hooks';
import { Button, Card, Pill, Screen } from '../components/ui';
import { connectHealth, healthName, syncHealth } from '../health/sync';
import { colors, type } from '../theme';

/** One screen for every way a watch run can reach STRYDE. */
export default function Devices() {
  const integrations = useIntegrations();
  const me = useMe();
  const updateMe = useUpdateMe();
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const doHealth = async () => {
    setBusy('health');
    setMsg(null);
    try {
      if (!(await connectHealth())) {
        setMsg(`${healthName} permission was not granted.`);
        return;
      }
      const n = await syncHealth();
      setMsg(n ? `Sent ${n} watch run${n > 1 ? 's' : ''}. Results appear in a few seconds.` : 'No new watch runs with GPS found.');
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'Sync failed');
    } finally {
      setBusy(null);
    }
  };

  const doFile = async () => {
    const res = await DocumentPicker.getDocumentAsync({ type: '*/*', copyToCacheDirectory: true });
    if (res.canceled) return;
    const file = res.assets[0];
    setBusy('file');
    try {
      const form = new FormData();
      form.append('file', { uri: file.uri, name: file.name, type: file.mimeType ?? 'application/octet-stream' } as unknown as Blob);
      const out = await api<{ id: number }>('/api/activities/import-file/', { form });
      router.push({ pathname: '/run/[activityId]', params: { activityId: String(out.id) } });
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setBusy(null);
    }
  };

  const doCloud = async (provider: string) => {
    try {
      const { url } = await api<{ url: string }>(`/api/integrations/${provider}/connect/`);
      await WebBrowser.openBrowserAsync(url);
      integrations.refetch();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'Not available yet');
    }
  };

  const onDevice = integrations.data?.on_device.filter((d) => d.platform === 'all' || d.platform === Platform.OS) ?? [];

  return (
    <Screen edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={{ padding: 20 }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={type.h1}>Watches</Text>
          <Text onPress={() => router.back()} style={{ color: colors.volt, fontSize: 16 }}>
            Done
          </Text>
        </View>
        <Text style={[type.small, { marginTop: 8 }]}>Runs from any watch count on STRYDE routes. Every run gets the same checks as a phone run.</Text>

        <Card style={{ marginTop: 18, flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          <View style={{ flex: 1 }}>
            <Text style={type.h3}>Post watch runs to leaderboards</Text>
            <Text style={type.small}>Watch runs on a route can win titles and points.</Text>
          </View>
          <Switch
            value={!!me.data?.post_watch_runs}
            onValueChange={(v) => updateMe.mutate({ post_watch_runs: v })}
            trackColor={{ true: colors.volt, false: colors.surface3 }}
          />
        </Card>

        {onDevice.map((d) => (
          <Card key={d.key} style={{ marginTop: 12 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Text style={type.h3}>{d.name}</Text>
              <Pill tone="volt" label="Ready" />
            </View>
            <Text style={[type.small, { marginTop: 4 }]}>{d.covers}</Text>
            <View style={{ marginTop: 12 }}>
              {d.key === 'file' ? (
                <Button small variant="secondary" title="Upload .FIT / .GPX / .TCX" loading={busy === 'file'} onPress={doFile} />
              ) : (
                <Button small title={`Connect & sync ${d.name}`} loading={busy === 'health'} onPress={doHealth} />
              )}
            </View>
          </Card>
        ))}

        <Text style={[type.h2, { marginTop: 24 }]}>Connect directly</Text>
        <Text style={[type.small, { marginTop: 4 }]}>Runs sync from the brand's cloud, no phone needed.</Text>
        {integrations.data?.cloud.map((c) => (
          <Card key={c.key} style={{ marginTop: 10, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
            <Text style={type.h3}>{c.name}</Text>
            {c.connected ? (
              <Pill tone="volt" label="Connected" />
            ) : c.available ? (
              <Button small title="Connect" onPress={() => doCloud(c.key)} />
            ) : (
              <Pill label="Coming soon" />
            )}
          </Card>
        ))}

        {msg && <Text style={{ color: colors.text, marginTop: 16 }}>{msg}</Text>}

        <View style={{ marginTop: 32 }}>
          <Button variant="secondary" title="Sign out" onPress={signOut} />
        </View>
      </ScrollView>
    </Screen>
  );
}
