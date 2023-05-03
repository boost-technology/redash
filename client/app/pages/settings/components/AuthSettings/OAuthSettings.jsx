import React from "react";
import Form from "antd/lib/form";
import Input from "antd/lib/input";
import Skeleton from "antd/lib/skeleton";
import Radio from "antd/lib/radio";
import DynamicComponent from "@/components/DynamicComponent";
import { SettingsEditorPropTypes, SettingsEditorDefaultProps } from "../prop-types";

import { isEmpty, join } from "lodash";
import Select from "antd/lib/select";
import Alert from "antd/lib/alert";

export default function OAuthSettings(props) {
  const { values, onChange, loading } = props;

  const onChangeEnabledStatus = e => {
    const updates = { auth_oauth_enabled: !!e.target.value };
    if (e.target.value) {
      updates.auth_oauth_type = e.target.value;
    }
    onChange(updates);
  };

  return (
    <DynamicComponent name="OrganizationSettings.OAuthSettings" {...props}>
      <h4>OAuth</h4>
      <Form.Item label="OAuth Enabled">
        {loading ? (
          <Skeleton title={{ width: 300 }} paragraph={false} active />
        ) : (
          <Radio.Group
            onChange={onChangeEnabledStatus}
            value={values.auth_oauth_enabled}>
            <Radio value={false}>Disabled</Radio>
            <Radio value={true}>Enabled</Radio>
          </Radio.Group>
        )}
      </Form.Item>
        {values.auth_oauth_enabled && (
            <>
              <Form.Item label="OAuth Provider Name">
                <Input
                  value={values.auth_oauth_name}
                  onChange={e => onChange({ auth_oauth_name: e.target.value })}
                />
              </Form.Item>
              <Form.Item label="OAuth URL">
                <Input
                  value={values.auth_oauth_url}
                  onChange={e => onChange({ auth_oauth_url: e.target.value })}
                />
              </Form.Item>
              <Form.Item label="OAuth Client ID">
                <Input
                  value={values.auth_oauth_client_id}
                  onChange={e => onChange({ auth_oauth_client_id: e.target.value })}
                />
              </Form.Item>
              <Form.Item label="OAuth Client Secret">
                <Input
                  value={values.auth_oauth_client_secret}
                  onChange={e => onChange({ auth_oauth_client_secret: e.target.value })}
                />
              </Form.Item>
              <Form.Item label="Allowed Email Domains">
                <Select
                mode="tags"
                value={values.auth_oauth_domains}
                onChange={value => onChange({ auth_oauth_domains: value })}
                />
                {!isEmpty(values.auth_oauth_domains) && (
                <Alert
                    message={
                    <p>
                        Any user registered with a <strong>{join(values.auth_oauth_domains, ", ")}</strong> email domain authenticated by the OAuth app will be able to login. If they don't have an existing user, a new user will be created and join
                        the <strong>Default</strong> group.
                    </p>
                    }
                    className="m-t-15"
                />
                )}
            </Form.Item>
            </>
          )}
    </DynamicComponent>
  );
}

OAuthSettings.propTypes = SettingsEditorPropTypes;

OAuthSettings.defaultProps = SettingsEditorDefaultProps;
