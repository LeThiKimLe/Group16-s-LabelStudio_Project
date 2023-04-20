import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { LsPlus } from "../../../assets/icons";
import { Button } from "../../../components";
import { Description } from "../../../components/Description/Description";
import { Input } from "../../../components/Form";
import { modal } from "../../../components/Modal/Modal";
import { Space } from "../../../components/Space/Space";
import { useAPI } from "../../../providers/ApiProvider";
import { useConfig } from "../../../providers/ConfigProvider";
import { Block, Elem } from "../../../utils/bem";
import { copyText } from "../../../utils/helpers";
import "./PeopleInvitation.styl";
import { PeopleList } from "./PeopleList";
import "./PeoplePage.styl";
import { SelectedUser } from "./SelectedUser";
// TODO Cần sửa chỗ này nữa, cũng thuộc giao diện, nút thêm People
const InvitationModal = ({ link }) => {
  // defined the array of data
  listRole = [
    { id: '2', Role: 'Administrator' },
    { id: '3', Role: 'Manager' },
    { id: '4', Role: 'Annotator' }
    ];
  // maps the appropriate column to fields property
  fields = { text: 'Role', value: 'id' };

    return (
      <Block name="invite">
        <Input
          value={link}
          style={{ width: '100%' }}
          readOnly
        />

      <Input
        label={"Email"}
        value={text}
        style={{ width: '100%' }}
      />

      <ComboBoxComponent id="comboelement" fields={fields} dataSource={listRole} allowCustom={true} placeholder="Select a role" defaultSelected="Annotator" />;

      <Description style={{ width: '70%', marginTop: 16 }}>
        Invite people to join your Label Studio instance. Enter email and Role for invited people. <a href="https://labelstud.io/guide/signup.html">Learn more</a>.
      </Description>
    </Block>
  );
};

export const PeoplePage = () => 
{
  const api = useAPI();
  const inviteModal = useRef();
  const config = useConfig();
  const [selectedUser, setSelectedUser] = useState(null);

  const [link, setLink] = useState();

  const selectUser = useCallback((user) => {
    setSelectedUser(user);

    localStorage.setItem('selectedUser', user?.id);
  }, [setSelectedUser]);

  const setInviteLink = useCallback((link) => {
    const hostname = config.hostname || location.origin;
    setLink(`${hostname}${link}`);
  }, [config, setLink]);

  const updateLink = useCallback(() => {
    api.callApi('resetInviteLink').then(({ invite_url }) => {
      setInviteLink(invite_url);
    });
  }, [setInviteLink]);

  // TODO Gọi API thêm người vào chỗ này để lấy ds pending member sau khi thêm xong + Có thể add thêm nút hiện pending member để có cớ gọi API
  const addPeopleLink = useCallback(() => {
    api.callApi('addPeopleLink')
  }, []);

  const inviteModalProps = useCallback((link) => ({
    title: "Invite people",
    style: { width: 640, height: 472 },
    body: () => (
      <InvitationModal link={link}/>
    ),
    footer: () => {
      const [copied, setCopied] = useState(false);

      const copyLink = useCallback(() => {
        setCopied(true);
        copyText(link);
        setTimeout(() => setCopied(false), 1500);
      }, []);

      return (
        <Space spread>
          <Space>
            <Button style={{ width: 170 }} onClick={() => addPeopleLink()}>
              Add People to Organization
            </Button>
          </Space>
          <Space>
            <Button style={{ width: 170 }} onClick={() => updateLink()}>
              Reset Link
            </Button>
          </Space>
          <Space>
            <Button primary style={{ width: 170 }} onClick={copyLink}>
              {copied ? "Copied!" : "Copy link"}
            </Button>
          </Space>
        </Space>
      );
    },
    bareFooter: true,
  }), []);

  const showInvitationModal = useCallback(() => {
    inviteModal.current = modal(inviteModalProps(link));
  }, [inviteModalProps, link]);

  const defaultSelected = useMemo(() => {
    return localStorage.getItem('selectedUser');
  }, []);

  useEffect(() => {
    api.callApi("inviteLink").then(({ invite_url }) => {
      setInviteLink(invite_url);
    });
  }, []);

  useEffect(() => {
    inviteModal.current?.update(inviteModalProps(link));
  }, [link]);

  return (
    <Block name="people">
      <Elem name="controls">
        <Space spread>
          <Space></Space>
          <Space>
            <Button icon={<LsPlus/>} primary onClick={showInvitationModal}>
              Add People
            </Button>
          </Space>
          <Space>
            <Button icon={<LsPlus/>} primary onClick={showInvitationModal}>
              Show Pending Member
            </Button>
          </Space>
        </Space>
      </Elem>
      <Elem name="content">
        <PeopleList
          selectedUser={selectedUser}
          defaultSelected={defaultSelected}
          onSelect={(user) => selectUser(user)}
        />

        {selectedUser && (
          <SelectedUser
            user={selectedUser}
            onClose={() => selectUser(null)}
          />
        )}

         
      </Elem>
    </Block>
  );
};

PeoplePage.title = "People";
PeoplePage.path = "/";
